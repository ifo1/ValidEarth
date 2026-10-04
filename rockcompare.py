import os
import numpy as np
import matplotlib.pyplot as plt

from colouredstrings import error, red

Nsigma = 3

def find_matching_rocks(refrocks, inputrocks, verbose = False):
    """
    For each input rock, find reference lithologies for which all
    available input property bounds are contained within the
    corresponding reference property bounds.

    Input rocks are identified by .name.
    Reference rocks are identified by .lithology.

    Returns:
        dict: {input_rock_name: [matching_lithologies]}
    """

    matches = {}

    for inp in inputrocks:

        # get a list of all parameters for the given rock
        input_props = {
            p.parameter: p
            for p in inp.properties
            if p.mean is not None
        }

        matching = []

        # for each reference rock
        for ref in refrocks:

            ref_props = {
                p.parameter: p
                for p in ref.properties
            }

            ok = False
            # for each physical property of the input rocks
            for parameter, ip in input_props.items():

                rp = ref_props.get(parameter)

                if rp is None:
                    continue

                # Input interval

                input_min = ip.min if ip.min is not None else ip.mean
                input_max = ip.max if ip.max is not None else ip.mean

                # Reference interval
                if rp.min is not None:
                    ref_min = rp.min
                elif rp.stdev is not None:
                    ref_min = rp.mean - Nsigma * rp.stdev
                else:
                    ref_min = rp.mean

                if rp.max is not None:
                    ref_max = rp.max
                elif rp.stdev is not None:
                    ref_max = rp.mean + Nsigma * rp.stdev
                else:
                    ref_max = rp.mean

                # At least part of the interval is within the bounds
                if not np.isfinite(ref_min) or not np.isfinite(ref_max) :
                    continue

                if input_min > ref_max or input_max < ref_min:
                    # remove from the list if anything contradicts
                    if ref.lithology in matching:
                        if verbose: print (inp.name + ": removing " + ref.lithology + " based on the " + parameter + " from " + ref.citation)
                        matching.remove(ref.lithology)
                    ok = False
                    break

                ok = True

            #print (inp.name + ": parameter " + parameter + " minmax " + str(input_min) + " " + str(input_max) + \
            #        " vs " + ref.lithology + " [" + ref.citation + "] with minmax " + str(ref_min) + " " + str(ref_max) + ": " + str(ok))

            if ok:
                if ref.lithology not in matching:
                    matching.append(ref.lithology)
        if not matching:
            print (error() + "Cannot find a reference sample matching rock '" + red(inp.name) + "' with the following properties: ", end='')
            for prop in inp.properties:
                print(str(prop.parameter) + " = " + str(prop.mean) + " ", end='')
            print('')
        inp.matching = matching


def plot_rock_properties( refrocks, inputrocks, output_dir="rock_plots", show_all = False):
    os.makedirs(output_dir, exist_ok=True)

    for inp in inputrocks:

        for ip in inp.properties:

            if ip.mean is None:
                continue

            parameter = ip.parameter

            # ----------------------------------------------------------
            # Collect reference rocks grouped by lithology
            # ----------------------------------------------------------

            groups = {}

            for ref in refrocks:

                rp = next(
                    (
                        p for p in ref.properties
                        if p.parameter == parameter
                    ),
                    None,
                )

                # show only matching rocks:
                if not show_all:
                    if inp.matching:
                        if not ref.lithology in inp.matching:
                            # print (inp.name + ": reference " + ref.lithology + " while matching are " + str(inp.matching) + " so " + str(ref.lithology in inp.matching))
                            continue

                if rp is None:
                    continue

                if rp.min is not None:
                    ref_min = rp.min
                elif rp.stdev is not None:
                    ref_min = rp.mean - Nsigma * rp.stdev
                else:
                    ref_min = rp.mean

                if rp.max is not None:
                    ref_max = rp.max
                elif rp.stdev is not None:
                    ref_max = rp.mean + Nsigma * rp.stdev
                else:
                    ref_max = rp.mean

                # show only overlapping
                if not show_all:
                    if not np.isfinite(ref_max) or not np.isfinite(ref_min): continue
                    if ip.mean < ref_min or ip.mean > ref_max: continue

                groups.setdefault(ref.lithology, []).append(
                    (ref, rp, ref_min, ref_max)
                )

            if not groups:
                continue

            # ----------------------------------------------------------
            # Figure
            # ----------------------------------------------------------

            fig, ax = plt.subplots(figsize=(12, 7))

            lithologies = list(groups.keys())
            n_lithologies = len(lithologies)

            group_width = 0.8

            # One colour per lithology
            cmap = plt.get_cmap("tab10")

            # ----------------------------------------------------------
            # Reference rocks
            # ----------------------------------------------------------

            for i, lithology in enumerate(lithologies):

                rocks = groups[lithology]
                n = len(rocks)

                if n == 1:
                    positions = np.array([i])
                else:
                    positions = np.linspace(
                        i - group_width / 4,
                        i + group_width / 4,
                        n,
                    )

                width = group_width / max(n, 1) * 0.75

                colour = cmap(i % 10)

                for position, (ref, rp, ref_min, ref_max) in zip( positions, rocks ):

                    # Full min-max interval
                    ax.bar(
                        position,
                        ref_max - ref_min,
                        bottom=ref_min,
                        width=width,
                        color=colour,
                        alpha=0.25,
                    )

                    # Mean and standard deviation
                    if rp.stdev is not None:
                        ax.errorbar(
                            position,
                            rp.mean,
                            yerr=rp.stdev,
                            fmt="o",
                            color=colour,
                            ecolor=colour,
                            capsize=4,
                        )
                    elif rp.mean is not None:
                        ax.plot(
                            position,
                            rp.mean,
                            "o",
                            color=colour,
                        )

            # ----------------------------------------------------------
            # Input-rock value
            #
            # Horizontal lines span the entire plot. No extra x-axis
            # bin is created for the input rock.
            # ----------------------------------------------------------

            # Actual value
            ax.axhline(
                ip.mean,
                linestyle="-",
                linewidth=2,
                color='black',
                label=f"{inp.name}: value",
            )

            # Standard deviation
            if ip.stdev is not None:

                ax.axhline(
                    ip.mean + ip.stdev,
                    linestyle="--",
                    color='black',
                    linewidth=1.2,
                    label=f"{inp.name}: ±1σ",
                )

                ax.axhline(
                    ip.mean - ip.stdev,
                    linestyle="--",
                    color='black',
                    linewidth=1.2,
                )

            # Explicit minimum and maximum
            if ip.min is not None:

                ax.axhline(
                    ip.min,
                    linestyle="-",
                    color='black',
                    linewidth=1,
                    label=f"{inp.name}: min/max",
                )

            if ip.max is not None:

                ax.axhline(
                    ip.max,
                    linestyle="-",
                    linewidth=1,
                )

            # ----------------------------------------------------------
            # Axes
            # ----------------------------------------------------------

            ax.set_xticks(np.arange(n_lithologies))
            ax.set_xticklabels(
                lithologies,
                rotation=45,
                ha="right",
            )

            ax.set_ylabel(parameter)
            ax.set_title(f"{inp.name} — {parameter}")

            ax.grid(
                axis="y",
                alpha=0.3,
            )

            ax.legend()

            fig.tight_layout()

            # ----------------------------------------------------------
            # Save
            # ----------------------------------------------------------

            safe_name = (
                f"{inp.name}_{parameter}"
                .replace("/", "_")
                .replace("\\", "_")
                .replace(" ", "_")
            )

            fig.savefig(
                os.path.join(
                    output_dir,
                    f"{safe_name}.pdf",
                ),
                bbox_inches="tight",
            )

            plt.close(fig)

