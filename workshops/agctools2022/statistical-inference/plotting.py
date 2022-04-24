import glob
import json
import re
import shlex
import subprocess
from collections import namedtuple

import numpy as np
from descartes import PolygonPatch
from shapely.geometry.polygon import Polygon

from interpolate import main as interpolate_main


def harvest_from_result(results_dict):
    harvests = {
        key: {
            "CLs": values["CLs_obs"],
            "CLsexp": values["CLs_exp"][2],
            "clsd1s": values["CLs_exp"][1],
            "clsd2s": values["CLs_exp"][0],
            "clsu1s": values["CLs_exp"][3],
            "clsu2s": values["CLs_exp"][4],
            "mn1": values["mass_hypotheses"][0],
            "mn2": values["mass_hypotheses"][1],
            "failedstatus": 0,
            "upperLimit": -1,
            "expectedUpperLimit": -1,
        }
        for key, values in results_dict.items()
    }

    return harvests


def make_interpolated_results(results):
    # d = {
    #     "figureOfMerit": "CLsexp",
    #     "modelDef": "mn2,mn1",
    #     "ignoreTheory": True,
    #     "ignoreUL": True,
    #     "debug": False,
    # }
    # args = namedtuple("Args", d.keys())(**d)
    # multiplex_data = multiplex_main(args, inputDataList=dataList).to_dict(
    #     orient="records"
    # )

    kwargs = {
        "nominalLabel": "Nominal",
        "xMin": None,
        "xMax": None,
        "yMin": None,
        "yMax": None,
        "smoothing": "0.02",
        # "smoothing": "0.07",
        "areaThreshold": 0,
        "xResolution": 100,
        "yResolution": 100,
        "xVariable": "mn1",
        "yVariable": "mn2",
        "closedBands": False,
        "forbiddenFunction": "x",
        "debug": False,
        "logX": False,
        "logY": False,
        "noSig": False,
        "interpolation": "multiquadric",
        # "interpolationEpsilon": 0,
        "interpolationEpsilon": 0.05,
        "level": 1.64485362695,
        "useROOT": False,
        "sigmax": 5,
        "useUpperLimit": False,
        "ignoreUncertainty": False,
        "fixedParamsFile": "",
    }
    args = namedtuple("Args", kwargs.keys())(**kwargs)
    # r = interpolate_main(args, multiplex_data)

    harvests = harvest_from_result(results)

    return interpolate_main(args, inputData=harvests)


def make_plot(ax, results, **kwargs):

    if kwargs.get("showPoints", False):
        mass_ranges = np.asarray(
            [values["mass_hypotheses"] for _, values in results.items()]
        ).T
        ax.scatter(*mass_ranges, s=20, alpha=0.2)

    if kwargs.get("showInterPolated", False):
        interpolated_bands = make_interpolated_results(results)
        if interpolated_bands is None:
            print("ERROR: interpolation failed")
            return 1

        if "Band_1s_0" not in interpolated_bands:
            print("ERROR: Band_1s_0 not included in interpolation bands")
            return 1

        # Expand the transverse of the array into the x,y components of the sequence
        # for the shell arg of Polygon
        ax.add_patch(
            PolygonPatch(
                Polygon(np.stack([*interpolated_bands["Band_1s_0"].T]).T),
                alpha=0.5,
                facecolor=kwargs.get("color", "steelblue"),
                label=r"Expected Limit ($\pm1\sigma$)",
            ),
        )

        # Expand the transverse of the array into x,y args of plot
        ax.plot(
            *interpolated_bands["Exp_0"].T,
            color="black",
            linestyle="dashed",
            alpha=0.5,
        )

        ax.plot(
            *interpolated_bands["Obs_0"].T,
            color="maroon",
            linewidth=2,
            linestyle="solid",
            alpha=0.5,
            label="Observed Limit",
        )

    # apply_decorations(ax, kwargs["label"])


def apply_decorations(ax, label):
    # ax.set_xlim(300, 1700)
    # ax.set_ylim(200, 1700)
    # dictionaries to hold the styles for re-use
    text_fd = dict(ha="left", va="center")
    atlas_fd = dict(weight="bold", style="italic", size=24, **text_fd)
    internal_fd = dict(size=24, **text_fd)

    # actually drawing the text
    ax.text(0.05, 0.9, "ATLAS", fontdict=atlas_fd, transform=ax.transAxes)
    ax.text(0.23, 0.9, label, fontdict=internal_fd, transform=ax.transAxes)

    ax.text(
        0.05,
        0.8,
        "$\sqrt{s} = 13\ \mathrm{TeV}, 139\ \mathrm{fb}^{-1}$\n All limits at 95% CL",
        fontdict=text_fd,
        transform=ax.transAxes,
    )
    # ax.text(
    #     0.0,
    #     1.035,
    #     r"$\tilde{b}_1\tilde{b}_1$ production ; $\tilde{b}_1\to b \tilde{\chi}_2^0$; $m(\tilde{\chi}_1^0)$ = 60 GeV",
    #     fontdict=text_fd,
    #     transform=ax.transAxes,
    # )

    # ax.text(
    #     350,
    #     750,
    #     r"Kinematically Forbidden $m(\tilde{\chi}_2^0)>m(\tilde{b}_1)$",
    #     rotation=35.0,
    #     fontdict=dict(ha="left", va="center", size=15, color="grey"),
    # )
    # ax.set_xlabel(
    #     r"$m(\tilde{b}_1)$ [GeV]", fontdict=dict(ha="right", va="center", size=20)
    # )
    # ax.set_ylabel(
    #     r"$m(\tilde{\chi}_2^0)$ [GeV]", fontdict=dict(ha="right", va="center", size=20)
    # )

    ax.legend(loc=(0.05, 0.6))
    ax.xaxis.set_label_coords(1.0, -0.1)
    ax.yaxis.set_label_coords(-0.15, 1.0)
    # ax.plot([200, 1400], [200, 1400], color="grey", linestyle="dashdot")


if __name__ == "__main__":
    main()
