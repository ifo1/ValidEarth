import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
import os.path

from colouredstrings import error, highlight

Nsigma = 1


def find_matching_rocks(refrocks, inputrocks, verbose=False):
    """
    Match input rocks against reference lithologies.

    A lithology matches an input rock when:
      1. At least one input property can be compared with reference data.
      2. For every input property available in the reference data,
         at least one reference entry contains the input interval.
      3. Reference entries with no corresponding input property are ignored.

    Stores:
        inp.matching:
            List of matching lithology names.

        inp.matching_citations:
            Dictionary:
            {lithology: {parameter: [matching citations]}}

    Returns:
        Dictionary mapping input rock names to matching lithologies.
    """

    # Group reference samples by lithology, preserving their original order.
    refs_by_lithology = defaultdict(list)

    for ref in refrocks:
        refs_by_lithology[ref.lithology].append(ref)

    matches = {}

    def finite(value):
        try:
            return value is not None and np.isfinite(value)
        except (TypeError, ValueError):
            return False

    def reference_interval(prop):
        """Return the reference interval, or None if unavailable."""

        if finite(prop.min):
            lower = prop.min
        elif finite(prop.mean) and finite(prop.stdev):
            lower = prop.mean - Nsigma * prop.stdev
        elif finite(prop.mean):
            lower = prop.mean
        else:
            return None

        if finite(prop.max):
            upper = prop.max
        elif finite(prop.mean) and finite(prop.stdev):
            upper = prop.mean + Nsigma * prop.stdev
        elif finite(prop.mean):
            upper = prop.mean
        else:
            return None

        if lower > upper:
            return None

        return lower, upper

    def input_interval(prop):
        """Return the input interval, or None if unavailable/inconsistent."""

        has_min = finite(prop.min)
        has_max = finite(prop.max)

        if has_min and has_max:
            if prop.min > prop.max:
                return None
            return prop.min, prop.max

        if not has_min and not has_max and finite(prop.mean):
            return prop.mean, prop.mean

        return None

    for inp in inputrocks:

        if verbose:
            print("Assessing " + highlight(inp.name))

        # Keep every input property with a usable value or interval.
        input_props = {
            p.parameter: p
            for p in inp.properties
            if (
                finite(p.mean)
                or finite(p.min)
                or finite(p.max)
            )
        }

        matching_lithologies = []
        matching_citations = {}

        for lithology, refs in refs_by_lithology.items():

            # Preserve the original genesis compatibility check.
            compatible_refs = [
                ref for ref in refs
                if not (
                    ref.genesis and inp.genesis
                    and not any(g in inp.genesis for g in ref.genesis)
                )
            ]

            if not compatible_refs:
                continue

            # Gather all reference entries for each input parameter.
            citations_by_parameter = {}
            failed = False
            compared_parameters = 0

            for parameter, ip in input_props.items():

                ip_interval = input_interval(ip)

                if ip_interval is None:
                    if verbose:
                        print(error() + "  Invalid or incomplete input interval for " + parameter)
                    failed = True
                    break

                # A parameter may occur in several reference samples.
                reference_entries = []

                for ref in compatible_refs:
                    for rp in ref.properties:
                        if rp.parameter == parameter:
                            interval = reference_interval(rp)
                            if interval is not None:
                                reference_entries.append(
                                    (ref, rp, interval)
                                )

                # No usable reference data for this property:
                # it cannot be used to accept or reject the lithology.
                if not reference_entries:
                    continue

                compared_parameters += 1
                ip_min, ip_max = ip_interval

                # Keep ALL reference citations whose intervals fully
                # contain the input interval.
                matching_entries = [
                    (ref, rp)
                    for ref, rp, (ref_min, ref_max)
                    in reference_entries
                    if ip_min >= ref_min and ip_max <= ref_max
                ]

                if verbose:
                    ref_min = min(interval[0] for _, _, interval in reference_entries)
                    ref_max = max(interval[1] for _, _, interval in reference_entries)
                    print(highlight(inp.name) + " " + parameter + " from " + str(ip_min) + " to " + str(ip_max) + 
                        f" --- matching {len(matching_entries)}/{len(reference_entries)} references for " + 
                        highlight(lithology) + f" with range from {ref_min} to {ref_max}"
                    )

                # Reference data exist, but none contains this property:
                # reject the entire lithology, regardless of other matches.
                if not matching_entries:
                    failed = True
                    break

                citations_by_parameter[parameter] = list(dict.fromkeys(
                    ref.citation
                    for ref, rp in matching_entries
                    if ref.citation is not None
                ))

            # Require at least one comparable parameter.
            if not failed and compared_parameters > 0:
                matching_lithologies.append(lithology)
                matching_citations[lithology] = citations_by_parameter

        inp.matching = matching_lithologies
        inp.matching_citations = matching_citations

        matches[inp.name] = matching_lithologies

        if verbose:
            for litho in matching_lithologies:
                print(highlight(inp.name) + " is matching " + highlight(litho) + " according to " , end='')
                for k, v in inp.matching_citations[litho].items():
                    print (k + " (" + " ".join(v) + ") ", end='')
                print ('')

    return matches


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
                    color='black',
                    linewidth=1,
                    label=f"{inp.name}: min/max",
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


def trimming(minval, maxval, vector, vector2):
    n = vector.size
    if n <= 200:
        return vector, vector2
    # leave no more than 100 points.
    d = (maxval-minval)/100.0
    ind = np.argsort(vector)
    svector2 = vector2[ind]
    svector = vector[ind]
    newvector = [svector[0]]
    newvector2  = [svector2[0]]
    for i in range(n-1):
        if svector[i+1] - newvector[-1] > d:
            newvector.append(svector[i+1])
            newvector2.append(svector2[i+1])
    return newvector, newvector2


def scatterplot_matrix(output_dir, rock, png, pngdpi, pdf, hist2d, hexbin):

    xlimmin = []
    xlimmax = []
    # a separate plot for each parameter
    for quantity in rock.properties:
        d = (quantity.max - quantity.min)/10
        if d == 0.0: d = quantity.mean/100.0
        xlimmin.append(quantity.min-d) 
        xlimmax.append(quantity.max+d) 

    n = len(rock.properties)
    fig, axes = plt.subplots(
        n, n, figsize=(2.5 * n, 2.5 * n),
        squeeze=False
    )

    fig.suptitle("Scatterplot Matrix for "+rock.name, fontsize=16, y=1.01)

    ticklabelfontsize=11
    axistitlefontsize=15


    for i in range(n):
        for j in range(n):
            ax = axes[i, j]

            if i > j:
                ax.set_visible(False)
                continue

            ax.ticklabel_format(style="plain", axis="x", useOffset=False)
            ax.ticklabel_format(style="plain", axis="y", useOffset=False)

            x = np.asarray(rock.properties[j].values, dtype=float)

            if i == j:
                ax.hist(
                    x[np.isfinite(x)], bins=30,
                    color="lightgray", edgecolor="black"
                )

                if rock.properties[j].stdev > 0:
                    ax.axvline(rock.properties[j].mean, color="black", linestyle="-")
                    for k in range(1,4):
                        ax.axvline(rock.properties[j].mean + k * rock.properties[j].stdev, color="black", linestyle="--", alpha=0.6)
                        ax.axvline(rock.properties[j].mean - k * rock.properties[j].stdev, color="black", linestyle="--", alpha=0.6)

                ax.set_yticklabels([])
                ax.set_xlim(xlimmin[j],xlimmax[j])
                ax.set_xlabel(rock.properties[i].parameter, fontsize=axistitlefontsize)
                ax.set_ylabel(rock.properties[i].parameter, fontsize=axistitlefontsize)

            else:
                y = np.asarray(rock.properties[i].values, dtype=float)
                valid = np.isfinite(x) & np.isfinite(y)

                if rock.properties[j].stdev == 0 and rock.properties[i].stdev == 0:
                    # Both variables are constant: plot a single point
                    ax.scatter(x[0], y[0], color="black", s=30)

                elif rock.properties[j].stdev == 0:
                    # X is constant: rug plot along the Y axis
                    ynew,xnew = trimming(xlimmin[i],xlimmax[i],y, x)
                    ax.plot( xnew,ynew ,  "_", color="black", markersize=6 )

                elif rock.properties[i].stdev == 0:
                    # Y is constant: rug plot along the X axis
                    xnew,ynew = trimming(xlimmin[j],xlimmax[j],x, y)
                    ax.plot( xnew,ynew ,  "|", color="black", markersize=6 )

                else:
                    if hist2d:
                        counts, xedges, yedges, im = ax.hist2d(x, y, bins=40, cmap='Greys', shading="flat",edgecolors="none",cmin=0)
                        xcenters = (xedges[:-1] + xedges[1:]) / 2
                        ycenters = (yedges[:-1] + yedges[1:]) / 2
                        ax.contour(xcenters, ycenters, counts.T, levels=[0.5], colors='black', linewidths=0.3)

                    if hexbin:
                        ax.hexbin(
                            x[valid], y[valid],
                            gridsize=40,
                            cmap="Greys",
                            mincnt=1,
                            edgecolors="black",
                            linewidths=0.3 )

                    if not (hexbin or hist2d):
                        ax.scatter(x[valid], y[valid], c='black', s=8, alpha=0.6)

                if valid.sum() > 1 and rock.properties[i].stdev > 0 and rock.properties[j].stdev > 0:
                    r = np.corrcoef(x[valid], y[valid])[0, 1]
                    ax.text(
                        0.7, 0.95, f"$R^2 = {r**2:.3f}$",
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
                ax.set_title(rock.properties[j].parameter, pad=6, fontsize=axistitlefontsize)
                ax.tick_params(axis="x", labeltop=True, direction="in", labelbottom=False, labelsize=ticklabelfontsize)
                ax.xaxis.set_ticks_position("top")

            if i == j == 0:
                ax.tick_params(axis="x", labeltop=True, direction="in", labelbottom=True, labelsize=ticklabelfontsize)

            # Tick labels and variable titles along the right boundary
            if j == n - 1:
                ax.tick_params(axis="y", labelright=True, labelleft=False, labelsize=ticklabelfontsize)
                ax.yaxis.set_ticks_position("both")

            if i != j:
                ax.tick_params(axis="both", which="both", direction="in", top=True, bottom=True, left=True, right=True, labelsize=ticklabelfontsize)



    # Minimise spacing between plots
    fig.subplots_adjust(
        left=0.08, right=0.92,
        bottom=0.08, top=0.92,
        wspace=0.05, hspace=0.05
    )

    if png:
        fig.savefig( os.path.join(output_dir, rock.name + ".png" ), bbox_inches="tight", dpi=pngdpi )
    if pdf:
        fig.savefig( os.path.join(output_dir, rock.name + ".pdf" ), bbox_inches="tight" )



