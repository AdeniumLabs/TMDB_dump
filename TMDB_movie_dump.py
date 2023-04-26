# coding: utf-8
import argparse
import json
import multiprocessing
import os
import requests
import time

from rich.console import Console
from rich.table import Table


def get_last_added_movie_id(api_key):
    latest_movie_url = f"https://api.themoviedb.org/3/movie/latest?api_key={api_key}"
    response = requests.get(latest_movie_url)
    return response.json()['id']


def download_movie_info_by_id(api_key, movie_id, path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)

        # Retrieve movie translations
        translations_url = f"https://api.themoviedb.org/3/movie/{movie_id}/translations?api_key={api_key}"
        response = requests.get(translations_url)
        if response.status_code != 200:
            with open(os.path.join(path, "errors.txt"), "a") as f:
                f.write(f'{str(movie_id)}-translations-{response.status_code}\n')
            return
        translations = response.json()["translations"]

        # Retrieve movie info in English
        movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        response = requests.get(movie_url)
        if response.status_code != 200:
            with open(os.path.join(path, "errors.txt"), "a") as f:
                f.write(f'{str(movie_id)}-language-{response.status_code}\n')
            return
        data = response.json()
        movie_info = data 


        # Extract language info from translations
        language_info = {}
        language_info["en-US"] = {'title': movie_info['title'], 'overview': movie_info['overview'], 'tagline': movie_info['tagline']}
        for translation in translations:
            if(language_info != "en-US"):
                data = translation["data"]
                language = f"{translation['iso_639_1']}-{translation['iso_3166_1']}"
                title =  data['title'] if data['title'] != "" else language_info["en-US"]['title']
                language_info[language] = {'title': title, 'overview': data['overview'], 'tagline': data['tagline']}


        # Remove redundant info from movie_info and add language_info
        movie_info.pop('title', None)
        movie_info.pop('overview', None)
        movie_info.pop('tagline', None)
        movie_info['language_info'] = language_info


        # Retrieve the credits information
        credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={api_key}"
        response = requests.get(credits_url)
        if response.status_code != 200:
            with open(os.path.join(path, "errors.txt"), "a") as f:
                f.write(f'{str(movie_id)}-credits-{response.status_code}\n')
            return

        data = response.json()
        movie_info['credits'] = {'cast': data['cast'], 'crew': data['crew']}

        # Save all movie info to a single JSON file
        with open(os.path.join(path, f"{movie_id}.json"), "w", encoding='utf-8') as outfile:
            json.dump({'languages': list(language_info.keys()), 'movie_info': movie_info}, outfile, ensure_ascii=False)
    except Exception as e:
        with open(os.path.join(path, "errors.txt"), "a") as f:
            f.write(f'{str(movie_id)}-exception-{str(e)}\n')
        time.sleep(4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--api_key", type=str, required=True, help="Your API key")
    parser.add_argument("--path", type=str, default="movies", help="The path to save the JSON files")
    parser.add_argument("--start_movie_id", type=int, default=1, help="The starting movie ID")
    parser.add_argument("--end_movie_id", type=int, default=None, help="The ending movie ID")
    parser.add_argument("--batch_size", type=int, default=1000, help="The batch size for movie ID ranges")
    parser.add_argument("--num_processes", type=int, default=multiprocessing.cpu_count(), help="Number of processes to use for downloading.")
    args = parser.parse_args()
    
    if args.end_movie_id:
        movie_ids = range(args.start_movie_id, args.end_movie_id+1)
    else:
        args.end_movie_id = get_last_added_movie_id(args.api_key)
        movie_ids = range(args.start_movie_id, args.end_movie_id+1)

    console = Console()
    table = Table(show_header=True, header_style="bold", title="Program Arguments", title_justify="center")
    table.add_column("Argument", style="cyan", justify="right")
    table.add_column("Value", style="yellow", justify="left")
    table.add_row("Path", args.path)
    table.add_row("Start Movie ID", str(args.start_movie_id))
    table.add_row("End Movie ID", str(args.end_movie_id))
    table.add_row("Batch Size", str(args.batch_size))
    table.add_row("Number of Processes", str(args.num_processes))
    console.print(table)

    console.print(f"[yellow]Downloading movie info for movie IDs {args.start_movie_id}-{args.end_movie_id}...[/yellow]")
    
    ranges = [range(i, min(i+args.batch_size, args.end_movie_id+1)) for i in range(args.start_movie_id, args.end_movie_id+1, args.batch_size)]
    total_ranges = len(ranges)
    
    for index, r in enumerate(ranges, start=1):
        start_time = time.time()

        console.print(f"[cyan]Downloading range {index}/{total_ranges}...[/cyan]")
        pool = multiprocessing.Pool(processes=args.num_processes)
        movie_ids = r
        args_list = list(zip([args.api_key] * len(movie_ids), movie_ids, [args.path] * len(movie_ids)))
        pool.starmap(download_movie_info_by_id, args_list)
        pool.close()
        pool.join()

        end_time = time.time()
        elapsed_time = end_time - start_time
        console.print(f"[b]Range {index}/{total_ranges} downloaded in {elapsed_time:.2f}s.[/b]", style="green on black")

    console.print("[green]All ranges downloaded successfully.[/green]")