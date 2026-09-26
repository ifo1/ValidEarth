# created using ChatGPT Free Tier
# modified and validated by Ilya Fomin

import numpy as np


def create_ecm1(
    sed_file="Sed_ECM1.txt",
    ecm_file="ECM1.txt",
    output_file="ECM1_model.txt",
):
    # ------------------------------------------------------------------
    # Read input files
    # ------------------------------------------------------------------

    sed_dtype = [
        ("Numb", int),
        ("Lon", float),
        ("Lat", float),
        ("Sed", float),
        ("SedT1", float),
        ("SedT2", float),
        ("SedT3", float),
        ("SedVP1", float),
        ("SedVP2", float),
        ("SedVP3", float),
        ("SedVS1", float),
        ("SedVS2", float),
        ("SedVS3", float),
        ("SedRHO1", float),
        ("SedRHO2", float),
        ("SedRHO3", float),
    ]

    ecm_dtype = [
        ("Numb", int),
        ("Lon", float),
        ("Lat", float),
        ("Hcc", float),
        ("Sed", float),
        ("Hc", float),
        ("Type", str),
        ("DLy1", float),
        ("DLy2", float),
        ("DLy3", float),
        ("TLy1", float),
        ("TLy2", float),
        ("TLy3", float),
        ("VP1", float),
        ("VP2", float),
        ("VP3", float),
        ("VS1", float),
        ("VS2", float),
        ("VS3", float),
        ("VPN", float),
        ("VSN", float),
        ("RHO1", float),
        ("RHO2", float),
        ("RHO3", float),
        ("RHON", float),
    ]

    sed = np.loadtxt(
        sed_file,
        dtype=sed_dtype,
        skiprows=1,
    )

    ecm = np.loadtxt(
        ecm_file,
        dtype=ecm_dtype,
        skiprows=1,
    )

    # ------------------------------------------------------------------
    # Match records by Numb, Lon and Lat
    # ------------------------------------------------------------------

    if len(sed) != len(ecm):
        raise ValueError(
            f"Different number of records: "
            f"{len(sed)} in {sed_file}, "
            f"{len(ecm)} in {ecm_file}"
        )

    for i, (s, e) in enumerate(zip(sed, ecm)):

        if s["Numb"] != e["Numb"]:
            raise ValueError(
                f"Record {i}: Numb mismatch: "
                f"{s['Numb']} != {e['Numb']}"
            )

        if not np.isclose(s["Lon"], e["Lon"]):
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"longitude mismatch: {s['Lon']} != {e['Lon']}"
            )

        if not np.isclose(s["Lat"], e["Lat"]):
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"latitude mismatch: {s['Lat']} != {e['Lat']}"
            )

        # --------------------------------------------------------------
        # Consistency checks
        # --------------------------------------------------------------

        s["SedT1"] /= 1000
        s["SedT2"] /= 1000 
        s["SedT3"] /= 1000
        s["Sed"] /= 1000

        if not np.isclose(
            s["SedT1"] + s["SedT2"] + s["SedT3"],
            s["Sed"],
        ):
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"SedT1 + SedT2 + SedT3 != Sed"
            )

        if abs(s["Sed"]-e["Sed"]) > 0.001:
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"Sed mismatch: {s['Sed']} != {e['Sed']}"
            )

        if abs( e["Hc"] - e["Sed"] - e["Hcc"]) > 0.001:
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"Hc != Sed + Hcc"
            )

        if not np.isclose(e["DLy3"], e["Hc"]):
            raise ValueError(
                f"Record {i}, Numb {s['Numb']}: "
                f"DLy3 != Hc"
            )

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------

    with open(output_file, "w") as f:

        f.write("Name ECM1\n")

        for s, e in zip(sed, ecm):

            f.write(f"Longitude {s['Lon']}\n")
            f.write(f"Latitude {s['Lat']}\n")

            f.write("Depth Vp Vs Density\n")

            # ----------------------------------------------------------
            # Sediments
            # ----------------------------------------------------------

            if s["SedT1"] != 0:

                # Surface
                f.write(
                    f"{0.0:.2f} "
                    f"{s['SedVP1'] * 1000:.2f} "
                    f"{s['SedVS1'] * 1000:.2f} "
                    f"{s['SedRHO1'] * 1000:.2f}\n"
                )

                # Bottom of sediment layer 1
                f.write(
                    f"{s['SedT1'] * 1000:.2f} "
                    f"{s['SedVP1'] * 1000:.2f} "
                    f"{s['SedVS1'] * 1000:.2f} "
                    f"{s['SedRHO1'] * 1000:.2f}"
                )

            if s["SedT2"] != 0:

                f.write("\n")

                # Top of sediment layer 2
                f.write(
                    f"{s['SedT1'] * 1000:.2f} "
                    f"{s['SedVP2'] * 1000:.2f} "
                    f"{s['SedVS2'] * 1000:.2f} "
                    f"{s['SedRHO2'] * 1000:.2f}\n"
                )

                # Bottom of sediment layer 2
                f.write(
                    f"{(s['SedT1'] + s['SedT2']) * 1000:.2f} "
                    f"{s['SedVP2'] * 1000:.2f} "
                    f"{s['SedVS2'] * 1000:.2f} "
                    f"{s['SedRHO2'] * 1000:.2f}"
                )

            elif s["SedT1"] != 0:

                # Put "sediments" on the final existing sediment line
                f.write(" sediments\n")


            if s["SedT3"] != 0:

                f.write("\n")

                # Top of sediment layer 3
                f.write(
                    f"{(s['SedT1'] + s['SedT2']) * 1000:.2f} "
                    f"{s['SedVP3'] * 1000:.2f} "
                    f"{s['SedVS3'] * 1000:.2f} "
                    f"{s['SedRHO3'] * 1000:.2f}\n"
                )

                # Bottom of sediment layer 3
                f.write(
                    f"{s['Sed'] * 1000:.2f} "
                    f"{s['SedVP3'] * 1000:.2f} "
                    f"{s['SedVS3'] * 1000:.2f} "
                    f"{s['SedRHO3'] * 1000:.2f} sediments\n"
                )

            elif s["SedT2"] != 0:

                # Put "sediments" on the final existing sediment line
                f.write(" sediments\n")

            # ----------------------------------------------------------
            # Upper crust
            # ----------------------------------------------------------

            f.write(
                f"{e['Sed'] * 1000:.2f} "
                f"{e['VP1'] * 1000:.2f} "
                f"{e['VS1'] * 1000:.2f} "
                f"{e['RHO1'] * 1000:.2f}\n"
            )

            f.write(
                f"{e['DLy1'] * 1000:.2f} "
                f"{e['VP1'] * 1000:.2f} "
                f"{e['VS1'] * 1000:.2f} "
                f"{e['RHO1'] * 1000:.2f} crustupper\n"
            )

            # ----------------------------------------------------------
            # Middle crust
            # ----------------------------------------------------------

            f.write(
                f"{e['DLy1'] * 1000:.2f} "
                f"{e['VP2'] * 1000:.2f} "
                f"{e['VS2'] * 1000:.2f} "
                f"{e['RHO2'] * 1000:.2f}\n"
            )

            f.write(
                f"{e['DLy2'] * 1000:.2f} "
                f"{e['VP2'] * 1000:.2f} "
                f"{e['VS2'] * 1000:.2f} "
                f"{e['RHO2'] * 1000:.2f} crustmiddle\n"
            )

            # ----------------------------------------------------------
            # Lower crust / Moho
            # ----------------------------------------------------------

            f.write(
                f"{e['DLy2'] * 1000:.2f} "
                f"{e['VP3'] * 1000:.2f} "
                f"{e['VS3'] * 1000:.2f} "
                f"{e['RHO3'] * 1000:.2f}\n"
            )

            f.write(
                f"{e['DLy3'] * 1000:.2f} "
                f"{e['VP3'] * 1000:.2f} "
                f"{e['VS3'] * 1000:.2f} "
                f"{e['RHO3'] * 1000:.2f} Moho\n"
            )

            # ----------------------------------------------------------
            # Lithospheric mantle
            # ----------------------------------------------------------

            f.write(
                f"{e['Hc'] * 1000:.2f} "
                f"{e['VPN'] * 1000:.2f} "
                f"{e['VSN'] * 1000:.2f} "
                f"{e['RHON'] * 1000:.2f}\n"
            )

            f.write(
                f"{100000.0:.2f} "
                f"{e['VPN'] * 1000:.2f} "
                f"{e['VSN'] * 1000:.2f} "
                f"{e['RHON'] * 1000:.2f} mantlelitho\n"
            )

create_ecm1( "Sed_ECM1.txt", "ECM1.txt", "ECM1_model.dat" 
)
