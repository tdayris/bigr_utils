import pandas as pd
import matplotlib.pyplot as plt
import base64
import io
import argparse
import ast
from pathlib import Path
import numpy as np
from datetime import timedelta

# ========== CONFIG ==========
metrics_to_plot = ['mem_mb', 'max_rss', 'max_vms', 'wasted', 'efficiency', 'threads', 'cpu_time',
    'cpu_usage', 'mean_load', 'time_min', 's', 'runtime_seconds']

# Définitions des métriques (https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#benchmark-rules)
metric_definitions = {
    "mem_mb": "Reserved memory (in MB).",
    "max_rss": "Maximum physical memory used (Resident Set Size), in MB.",
    "max_vms": "Maximum virtual memory used (Virtual Memory Size), in MB.",
    "wasted": "Reserved but unused memory (wasted) based on Maximum virtual memory, in MB.",
    "efficiency": "Proportion of reserved memory actually used, based on Maximum virtual memory, in %.",
    "threads": "Number of reserved threads.",
    "cpu_time": "Total CPU time consumed (sum across all cores; user + system), in seconds.",
    "cpu_usage": "Percentage of CPU used, in %.",
    "mean_load": "CPU load = CPU time (cpu_usage) divided by wall clock time ('s').",
    "time_min": "Reserved time for a job, in minutes.",
    "s": "Execution duration, in seconds.",
    "runtime_seconds": "Actual execution duration, converted from h:m:s to seconds.",
    "io_in": "Total volume of data read by the job, in bytes.",
    "io_out": "Total volume of data written by the job, in bytes.",
    "input_size_mb": "Size of input files, in MB."
}

# ========== Fonctions utilitaires ==========
def hms_to_seconds(hms):
    try:
        t = str(hms)
        if ":" in t:
            h, m, s = t.split(":")
            return int(h)*3600 + int(m)*60 + float(s)
        return float(t)
    except:
        return None
        
def fmt_seconds(sec):
    if pd.isna(sec):
        return ""
    return str(timedelta(seconds=int(round(float(sec)))))

def build_group_stats(df):
    time_col = "s" if "s" in df.columns else ("hms_seconds" if "hms_seconds" in df.columns else None)
    agg_map = {"jobid": "count"}

    for c in ["max_rss","max_vms","mem_mb","wasted","efficiency","threads","cpu_time","cpu_usage","mean_load","time_min"]:
        if c in df.columns: agg_map[c] = "mean"
    if time_col:
        agg_map[time_col] = ["sum","min","max"]

    grouped = df.groupby("rule_name", dropna=False).agg(agg_map)
    # Flatten MultiIndex columns
    new_cols = []
    for col in grouped.columns.values:
        if isinstance(col, tuple):
            label = " (".join([str(c) for c in col if c is not None]) + ")"
        else:
            label = str(col)
        new_cols.append(label.strip("_"))
    grouped.columns = new_cols

    grouped = grouped.rename(columns={"jobid_count":"nb_jobs"}).reset_index()

    if time_col:
        for sub in ["sum","min","max"]:
            col = f"{time_col} ({sub})"
            if col in grouped.columns:
                grouped[f"{time_col} ({sub} hms)"] = grouped[col].apply(fmt_seconds)
                grouped.drop(columns=[col], inplace=True)

    #sort_cols = [c for c in [f"{time_col} (sum)","cpu_time (sum)","io_in (sum)"] if c in grouped.columns]
    #if sort_cols:
    #    grouped = grouped.sort_values(sort_cols[0], ascending=False)
    return grouped

def plot_metric(metric, df, group_col="rule_name"):
    fig, ax = plt.subplots(figsize=(12,4))
    for name, group in df.groupby(group_col):
        ax.plot(group.index, group[metric], marker="o", linestyle="-", label=name)
    ax.set_title(metric)
    ax.set_xlabel("")
    ax.set_ylabel(metric)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # légende externe
    ax.set_xticklabels([]) #masque les valeurs de l'axe des x
    fig.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

# ========== Main ==========
def main():
    parser = argparse.ArgumentParser(description="Génère un rapport HTML avec stats + graphes par règle.")
    parser.add_argument("input_csv", help="Fichier CSV en entrée")
    parser.add_argument("-o", "--output_html", default="rapport_stats.html", help="Fichier HTML de sortie")
    args = parser.parse_args()

    # Lecture CSV
    df = pd.read_csv(args.input_csv)
    df.columns = [str(c).strip() for c in df.columns]
    if "rule_name" not in df.columns:
        raise SystemExit("Colonne 'rule_name' absente du CSV.")

    # Conversion durées
    df["runtime_seconds"] = df["h:m:s"].apply(hms_to_seconds)

    # Conversion numérique
    for col in ["s", "max_rss", "max_vms","io_in", "io_out","mean_load","cpu_time","threads",
        "cpu_usage","input_size_mb", "efficiency","mem_mb","mem_gb", "wasted", "runtime"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Assemblage de time_min, walltime et/ou runtime dans la colonne time_min
    df["time_min"] = df["time_min"].fillna(df["walltime"])
    df.drop(columns=["walltime"], inplace=True)
    df["time_min"] = df["time_min"].fillna(df["runtime"])
    df.drop(columns=["runtime"], inplace=True)

    # Assemblage de mem_mb et mem_gb dans la colonne mem_mb
    df["mem_mb"] = df["mem_mb"].fillna(df["mem_gb"] * 1024)
    df.drop(columns=["mem_gb"], inplace=True)
    
    # Supprimer la colonne index
    df.drop(columns=["index"], inplace=True)
    df.drop(columns=["index.1"], inplace=True)
    
    # Ordonne les colonnes:
    df = df[['rule_name', 'wildcards', 'mem_mb', 'max_rss', 'max_vms', 'wasted', 'efficiency',
        'threads', 'cpu_time', 'cpu_usage', 'mean_load', 'time_min', 's', 'runtime_seconds', 
        'input_size_mb', 'io_in', 'io_out', 'jobid', 'max_uss', 'max_pss', 'params', 'resources']]
    
    # Agrégation par règle
    summary = build_group_stats(df) #.reset_index()
    
    # HTML
    css = '''
    <style>
        body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 2rem; }
        h1 { margin-bottom: 0; }
        .subtitle { color: #666; margin-top: .25rem; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; font-size: 0.95rem; }
        th, td { border: 1px solid #ddd; padding: .5rem .6rem; text-align: right; }
        th { background: #f5f5f7; position: sticky; top: 0; }
        td:first-child, th:first-child { text-align: left; }
        .pill { display: inline-block; background: #eef; color: #223; padding: .15rem .5rem; border-radius: 999px; font-size: .8rem; }
        .rule-section { margin-top: 2rem; }
        .kpi { display: inline-block; padding: .75rem 1rem; background: #fafafa; border: 1px solid #eee; border-radius: .75rem; margin-right: .75rem; }
        .muted { color: #777; }
        .small { font-size: .85rem; }
    </style>
    '''
    html_parts = ["<html><head><meta charset='utf-8'><title>Report of benchmark</title>", css, "</head><body>"]
    html_parts.append("<html><head><meta charset='utf-8'><title>Report Stats</title></head><body>")
    html_parts.append("<h1>Statistical report on snakemake pipeline execution</h1>")
    
    #Cellules de résumer: nombre total de cpu, etc
    total_cpu = df["cpu_time"].sum() if "cpu_time" in df.columns else np.nan
    total_io_in = df["io_in"].sum() if "io_in" in df.columns else np.nan
    total_io_out = df["io_out"].sum() if "io_out" in df.columns else np.nan
    kpi_html = "<div>"
    kpi_html += f'<div class="kpi"><div class="muted small">Number of unique rules</div><div><strong>{summary.shape[0]}</strong></div></div>'
    kpi_html += f'<div class="kpi"><div class="muted small">Number of jobs</div><div><strong>{df.shape[0]}</strong></div></div>'
    if not pd.isna(total_cpu):
        kpi_html += f'<div class="kpi"><div class="muted small">Total CPU time (sec)</div><div><strong>{total_cpu:,.0f}s</strong></div></div>'
    if not pd.isna(total_io_in):
        kpi_html += f'<div class="kpi"><div class="muted small">Total IO in (octets)</div><div><strong>{total_io_in:,.2f}</strong></div></div>'
    if not pd.isna(total_io_out):
        kpi_html += f'<div class="kpi"><div class="muted small">Total IO out (octets)</div><div><strong>{total_io_out:,.2f}</strong></div></div>'
    kpi_html += "</div>"
    html_parts.append(kpi_html)

    # Définitions
    html_parts.append("<h2>Mettrics definition</h2><ul>")
    for metric, desc in metric_definitions.items():
        html_parts.append(f"<li><b>{metric}</b> : {desc}</li>")
    html_parts.append("</ul>")

    # Tableau résumé
    html_parts.append("<h2>Summary per rule</h2>")
    html_parts.append(summary.to_html(index=False, float_format="%.2f"))

    # Graphiques
    html_parts.append("<h2>Graphs per metric</h2>")
    for metric in metrics_to_plot:
        img_b64 = plot_metric(metric, df)
        html_parts.append(f"<img src='data:image/png;base64,{img_b64}'/>")

    # Détails
    html_parts.append("<h2>Details per rule</h2>")
    for rule in df["rule_name"].unique():
        html_parts.append(f"<h3>{rule}</h3>")
        sub_df = df[df["rule_name"] == rule]
        html_parts.append(sub_df.to_html(index=False, float_format="%.2f"))

    html_parts.append("</body></html>")

    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

    print(f"HTML report generated : {args.output_html}")

if __name__ == "__main__":
    main()
