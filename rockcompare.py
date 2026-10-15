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

            # check that the rock type matches
            if ref.genesis and inp.genesis:
                if not any(map(lambda v: v in inp.genesis, ref.genesis)):
                    continue

            ok = False
            # for each physical property of the input rocks
            for parameter, ip in input_props.items():

                rp = ref_props.get(parameter)

                if rp is None:
                    continue

                # Input interval
                input_min = ip.min if np.isfinite(ip.min) else ip.mean
                input_max = ip.max if np.isfinite(ip.max) else ip.mean
                # print (parameter, input_min, input_max, ip.min, ip.mean, ip.max)

                # Reference interval
                if np.isfinite(rp.min):
                    ref_min = rp.min
                elif np.isfinite(rp.stdev):
                    ref_min = rp.mean - Nsigma * rp.stdev
                else:
                    ref_min = rp.mean

                if np.isfinite(rp.max):
                    ref_max = rp.max
                elif np.isfinite(rp.stdev):
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
                #    " vs " + ref.lithology + " [" + ref.citation + "] with minmax " + str(ref_min) + " " + str(ref_max) + ": " + str(ok))

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


def scatterplot_matrix(output_dir, filename, titles, arrays, means, sigmas, mins, maxs, png, pdf, hist2d, hexbin):

    n = len(titles)
    fig, axes = plt.subplots(
        n, n, figsize=(2.5 * n, 2.5 * n),
        squeeze=False
    )

    fig.suptitle("Scatterplot Matrix for "+filename, fontsize=16, y=1.01)

    ticklabelfontsize=11
    axistitlefontsize=15

    xlimmin = []
    xlimmax = []
    for i in range(n):
        d = (maxs[i] - mins[i])/10
        if d == 0.0: d = maxs[i]/100.0
        xlimmin.append(mins[i]-d) 
        xlimmax.append(maxs[i]+d) 

    for i in range(n):
        for j in range(n):
            ax = axes[i, j]

            if i > j:
                ax.set_visible(False)
                continue

            ax.ticklabel_format(style="plain", axis="x", useOffset=False)
            ax.ticklabel_format(style="plain", axis="y", useOffset=False)

            x = np.asarray(arrays[j], dtype=float)

            if i == j:
                ax.hist(
                    x[np.isfinite(x)], bins=30,
                    color="lightgray", edgecolor="black"
                )

                if sigmas[i] > 0:
                    ax.axvline(means[i], color="black", linestyle="-")
                    for k in range(1,4):
                        ax.axvline(means[i] + k * sigmas[i], color="black", linestyle="--", alpha=0.6)
                        ax.axvline(means[i] - k * sigmas[i], color="black", linestyle="--", alpha=0.6)

                ax.set_yticklabels([])
                ax.set_xlim(xlimmin[j],xlimmax[j])
                ax.set_xlabel(titles[i], fontsize=axistitlefontsize)
                ax.set_ylabel(titles[i], fontsize=axistitlefontsize)

            else:
                y = np.asarray(arrays[i], dtype=float)
                valid = np.isfinite(x) & np.isfinite(y)

                if sigmas[j] == 0 and sigmas[i] == 0:
                    # Both variables are constant: plot a single point
                    ax.scatter(x[0], y[0], color="black", s=30)

                elif sigmas[j] == 0:
                    # X is constant: rug plot along the Y axis
                    ax.plot(
                        np.full(len(y), x[0]), y,
                        "|", color="black", markersize=6
                    )

                elif sigmas[i] == 0:
                    # Y is constant: rug plot along the X axis
                    ax.plot(
                        x, np.full(len(x), y[0]),
                        "_", color="black", markersize=6
                    )

                else:
                    if hist2d:
                        H, xedges, yedges = np.histogram2d(x[valid], y[valid], 40)
                        H = np.ma.masked_equal(H, 1)
                        mesh = ax.pcolormesh(
                            xedges, yedges, H.T,
                            cmap="Greys",
                            shading="flat",
                            edgecolors="none",
                            linewidth=0
                        )

                    if hexbin:
                        ax.scatter(x[valid], y[valid], c='black', s=8, alpha=0.6)
                        ax.hexbin(
                            x[valid], y[valid],
                            gridsize=40,
                            cmap="Greys",
                            mincnt=1,
                            edgecolors="black",
                            linewidths=0.3 )

                    if not (hexbin or hist2d):
                        ax.scatter(x[valid], y[valid], c='black', s=8, alpha=0.6)

                if valid.sum() > 1 and sigmas[i] > 0 and sigmas[j] > 0:
                    r = np.corrcoef(x[valid], y[valid])[0, 1]
                    ax.text(
                        0.95, 0.95, f"$R^2 = {r**2:.3f}$",
                        transform=ax.transAxes,
                        ha="right", va="top", fontsize=ticklabelfontsize
                    )

                ax.set_xlim(xlimmin[j],xlimmax[j])
                ax.set_ylim(xlimmin[i],xlimmax[i])
                # Remove axis labels from non-diagonal plots
                ax.set_xlabel("")
                ax.set_ylabel("")
                if j < n-1: ax.set_yticklabels([])
                if i > 0: ax.set_xticklabels([])

            # Variable titles along the top boundary
            if i == 0:
                ax.set_title(titles[j], pad=6, fontsize=axistitlefontsize)
                ax.tick_params(axis="x", labeltop=True, direction="in", labelbottom=False, labelsize=ticklabelfontsize)
                ax.xaxis.set_ticks_position("top")

            if i == j == 0:
                ax.tick_params(axis="x", labeltop=True, direction="in", labelbottom=True, labelsize=ticklabelfontsize)

            # Tick labels and variable titles along the right boundary
            if j == n - 1:
                ax.tick_params(axis="y", labelright=True, labelleft=False, labelsize=ticklabelfontsize)
                ax.yaxis.set_ticks_position("both")

                #if i != j:
                    #ax.set_ylabel(titles[i], rotation=270, labelpad=12)
                    #ax.yaxis.set_label_position("right")

            if i != j:
                ax.tick_params(axis="both", which="both", direction="in", top=True, bottom=True, left=True, right=True, labelsize=ticklabelfontsize)



    # Minimise spacing between plots
    fig.subplots_adjust(
        left=0.08, right=0.92,
        bottom=0.08, top=0.92,
        wspace=0.05, hspace=0.05
    )

    if png:
        fig.savefig( os.path.join(output_dir, filename + ".png" ), bbox_inches="tight" )
    if pdf:
        fig.savefig( os.path.join(output_dir, filename + ".pdf" ), bbox_inches="tight" )



