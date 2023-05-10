# coding: utf-8
import argparse
import json
import multiprocessing
import os
import requests
import time

from rich.console import Console
from rich.table import Table

def get_last_added_tv_show_id(api_key):
    latest_tv_show_url = f"https://api.themoviedb.org/3/tv/latest?api_key={api_key}"
    response = requests.get(latest_tv_show_url)
    return response.json()['id']

def get_translate_linguages(api_key, tv_id, path):
    # Retrieve tv show translations
        translations_url = f"https://api.themoviedb.org/3/tv/{tv_id}/translations?api_key={api_key}"
        response = requests.get(translations_url)
        if response.status_code != 200:
            with open(os.path.join(path, "errors.txt"), "a") as f:
                f.write(f'{str(tv_id)}-translations-{response.status_code}\n')
            return
        translations = response.json()["translations"]
        languages = []
        for translation in translations:
            languages.append(f"{translation['iso_639_1']}-{translation['iso_3166_1']}")
        return languages


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", type=str, required=True, help="Your API key")
    parser.add_argument("--path", type=str, default="tv show", help="The path to save the JSON files")
    parser.add_argument("--start_tv_show_id", type=int, default=1, help="The starting tv show ID")
    parser.add_argument("--end_tv_show_id", type=int, default=None, help="The ending tv show ID")
    parser.add_argument("--batch_size", type=int, default=1000, help="The batch size for  ID ranges")
    parser.add_argument("--num_processes", type=int, default=multiprocessing.cpu_count(), help="Number of processes to use for downloading.")
    args = parser.parse_args()
    
    if args.end_tv_show_id:
        tv_show_ids = range(args.start_tv_show_id, args.end_tv_show_id+1)
    else:
        args.end_tv_show_id = get_last_added_tv_show_id(args.api_key)
        tv_show_ids = range(args.start_tv_show_id, args.end_tv_show_id+1)

    console = Console()
    table = Table(show_header=True, header_style="bold", title="Program Arguments", title_justify="center")
    table.add_column("Argument", style="cyan", justify="right")
    table.add_column("Value", style="yellow", justify="left")
    table.add_row("Path", args.path)
    table.add_row("Start tv show ID", str(args.start_tv_show_id))
    table.add_row("End tv show ID", str(args.end_tv_show_id))
    table.add_row("Batch Size", str(args.batch_size))
    table.add_row("Number of Processes", str(args.num_processes))
    console.print(table)

    console.print(f"[yellow]Downloading tv show info for tv_show IDs {args.start_tv_show_id}-{args.end_tv_show_id}...[/yellow]")
    
    ranges = [range(i, min(i+args.batch_size, args.end_tv_show_id+1)) for i in range(args.start_tv_show_id, args.end_tv_show_id+1, args.batch_size)]
    total_ranges = len(ranges)
    
    #for index, r in enumerate(ranges, start=1):
    #    start_time = time.time()

    #    console.print(f"[cyan]Downloading range {index}/{total_ranges}...[/cyan]")
    #    pool = multiprocessing.Pool(processes=args.num_processes)
    #    tv_show_ids = r
    #    args_list = list(zip([args.api_key] * len(tv_show_ids), tv_show_ids, [args.path] * len(tv_show_ids)))
    #    pool.starmap(download_tv_show_info_by_id, args_list)
    #    pool.close()
    #    pool.join()

    #    end_time = time.time()
    #    elapsed_time = end_time - start_time
    #    console.print(f"[b]Range {index}/{total_ranges} downloaded in {elapsed_time:.2f}s.[/b]", style="green on black")

    #console.print("[green]All ranges downloaded successfully.[/green]")

