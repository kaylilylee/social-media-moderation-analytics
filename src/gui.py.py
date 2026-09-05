"""
Interactive Tkinter dashboard for the Social Media Moderation Analytics project.
"""

import tkinter as tk
from tkinter import messagebox, ttk

import main


def write_log(message: str) -> None:
    """Write a message to the GUI log and persistent audit log."""
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    main.write_audit(message)


def load_data() -> None:
    try:
        main.prepare_data(force_reload=True)
        write_log("Datasets loaded and prepared successfully.")
        messagebox.showinfo(
            "Load Data",
            "Datasets loaded and prepared successfully.",
        )
    except Exception as exc:
        write_log(f"Error during loading: {exc}")
        messagebox.showerror("Error", str(exc))


def clean_data() -> None:
    try:
        main.prepare_data(force_reload=True)
        write_log(
            "Cleaning completed: missing values, duplicates and "
            "invalid references handled."
        )
        messagebox.showinfo(
            "Clean Data",
            "Cleaning completed successfully.",
        )
    except Exception as exc:
        write_log(f"Error during cleaning: {exc}")
        messagebox.showerror("Error", str(exc))


def transform_data() -> None:
    try:
        prepared = main.prepare_data(force_reload=True)
        main.save_json_backup(prepared)
        write_log(
            "Data transformed and JSON backup saved successfully."
        )
        messagebox.showinfo(
            "Transform Data",
            "Transformation completed and JSON backup saved.",
        )
    except Exception as exc:
        write_log(f"Error during transformation: {exc}")
        messagebox.showerror("Error", str(exc))


def run_statistics() -> None:
    try:
        metric = metric_dropdown.get()
        mean, median, mode = main.run_statistics(metric)

        write_log(f"Statistics requested for metric: {metric}")
        write_log(f"Mean: {mean}")
        write_log(f"Median: {median}")
        write_log(f"Mode: {mode}")

        messagebox.showinfo(
            "Statistics",
            f"Metric: {metric}\n"
            f"Mean: {mean}\n"
            f"Median: {median}\n"
            f"Mode: {mode}",
        )
    except Exception as exc:
        write_log(f"Error during statistics: {exc}")
        messagebox.showerror("Error", str(exc))


def run_visualisation() -> None:
    try:
        main.run_visualisation()
        write_log("Visualisations generated successfully.")
        write_log("Saved: outputs/report_correlation.png")
        write_log("Saved: outputs/report_heatmap.png")
        write_log("Saved: outputs/posting_pivot.png")
        write_log("Saved: outputs/categorical_analysis.png")
        messagebox.showinfo(
            "Visualisation",
            "Visualisations generated and saved in the outputs folder.",
        )
    except Exception as exc:
        write_log(f"Error during visualisation: {exc}")
        messagebox.showerror("Error", str(exc))


def run_full_analysis() -> None:
    try:
        metric = metric_dropdown.get()
        results = main.run_full_analysis(metric, force_reload=True)

        stats = results["statistics"]
        timings = results["timings"]

        write_log("Full analysis pipeline executed successfully.")
        write_log(f"Selected metric: {stats['metric']}")
        write_log(f"Mean: {stats['mean']}")
        write_log(f"Median: {stats['median']}")
        write_log(f"Mode: {stats['mode']}")
        write_log(
            f"Correlation value: {round(results['correlation'], 2)}"
        )
        write_log(
            f"Total pipeline time: "
            f"{timings['total_seconds']:.4f} seconds"
        )

        messagebox.showinfo(
            "Full Analysis",
            "Full analysis pipeline executed successfully.\n\n"
            f"Total time: {timings['total_seconds']:.4f} seconds",
        )
    except Exception as exc:
        write_log(f"Error occurred: {exc}")
        messagebox.showerror(
            "Error",
            f"Error in the analysis pipeline: {exc}",
        )


root = tk.Tk()
root.title("Social Media Moderation Analytics")
root.geometry("1000x680")

title = tk.Label(
    root,
    text="Moderation Analytics Dashboard",
    font=("Arial", 18, "bold"),
)
title.pack(pady=15)

subtitle = tk.Label(
    root,
    text=(
        "Load, prepare and analyse moderation data with "
        "auditable processing steps"
    ),
    font=("Arial", 10),
)
subtitle.pack(pady=(0, 8))

data_frame = tk.LabelFrame(
    root,
    text="Data Preparation",
    padx=12,
    pady=10,
)
data_frame.pack(pady=8)

tk.Button(
    data_frame,
    text="Load Data",
    width=15,
    command=load_data,
).grid(row=0, column=0, padx=8, pady=5)

tk.Button(
    data_frame,
    text="Clean Data",
    width=15,
    command=clean_data,
).grid(row=0, column=1, padx=8, pady=5)

tk.Button(
    data_frame,
    text="Transform Data",
    width=15,
    command=transform_data,
).grid(row=0, column=2, padx=8, pady=5)

analysis_frame = tk.LabelFrame(
    root,
    text="Analysis",
    padx=12,
    pady=10,
)
analysis_frame.pack(pady=8)

tk.Label(
    analysis_frame,
    text="Select Metric:",
    font=("Arial", 11),
).grid(row=0, column=0, padx=8, pady=5)

metric_dropdown = ttk.Combobox(
    analysis_frame,
    values=["like", "comment", "share", "report"],
    state="readonly",
    width=20,
)
metric_dropdown.grid(row=0, column=1, padx=8, pady=5)
metric_dropdown.current(0)

tk.Button(
    analysis_frame,
    text="Run Statistics",
    width=15,
    command=run_statistics,
).grid(row=0, column=2, padx=8, pady=5)

tk.Button(
    analysis_frame,
    text="Run Visualisation",
    width=15,
    command=run_visualisation,
).grid(row=0, column=3, padx=8, pady=5)

tk.Button(
    root,
    text="Run Full Analysis",
    width=20,
    command=run_full_analysis,
).pack(pady=10)

tk.Label(
    root,
    text="Audit Log",
    font=("Arial", 12, "bold"),
).pack(pady=(8, 4))

log_box = tk.Text(root, height=20, width=115)
log_box.pack(padx=15, pady=10)

write_log("System started.")
write_log("Ready for user actions.")

root.mainloop()
