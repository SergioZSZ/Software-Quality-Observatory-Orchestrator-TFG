import json
import os
import requests
from pathlib import Path


GITHUB_TIMEOUT = 30


def fetch(input, output, type, not_archived, not_forked, not_disabled):

    open(output, 'w')

    if os.path.isfile(input):
        with open(input) as org_list:
            for org in org_list.readlines():
                _fetch(org.rstrip("\n"), output, type,
                       not_archived, not_forked, not_disabled)
    else:
        _fetch(input, output, type, not_archived, not_forked, not_disabled)


def _fetch(name, out_path, type, not_archived, not_forked, not_disabled):

    if type not in ['orgs', 'users']:
        raise ValueError(f'Type {type} is not supported.')

    print(f"Fetching repositories from {type} {name}:")

    URL = f"https://api.github.com/{type}/{name}/repos"
    page_size = 100 #antes 50, pero soporta el doble, 1 request menos a githubapi
    page = 1
    PARAMS = {'per_page': page_size, 'page': page}
    # TOKEN
    hasToken = False
    try:
        if os.path.isfile(Path("~/.somef/config.json").expanduser()):
            with open(Path("~/.somef/config.json").expanduser()) as json_file:
                data = json.load(json_file)
        try:
            TOKEN = data['Authorization']
            HEADERS = {
                "accept": "application/vnd.github.v3+json",
                "Authorization": TOKEN
            }
            hasToken = True
        except:
            print("Please provide Valid Authorization Token\n")
            print("Will commence fetch WITHOUT token \n")
    except Exception as e:
        print(str(e))

    cont = True

    with open(out_path, 'a') as file_out:
        while cont:
            try:
                if not hasToken:
                    r = requests.get(
                        url=URL,
                        params=PARAMS,
                        timeout=GITHUB_TIMEOUT,
                    )
                else:
                    r = requests.get(
                        url=URL,
                        params=PARAMS,
                        headers=HEADERS,
                        timeout=GITHUB_TIMEOUT,
                    )

                # Interrumpir el fetch si GitHub responde con un error HTTP.
                # De este modo no se acepta como válido un repos.txt parcial.
                r.raise_for_status()

                data_repos = r.json()

                # La API debe devolver una lista de repositorios. Las respuestas
                # de error de GitHub suelen ser objetos con un campo "message".
                if not isinstance(data_repos, list):
                    raise RuntimeError(
                        f"Invalid GitHub response for {type} '{name}'"
                    )

                print("Request " + str(page) + ". " + str(len(data_repos)
                                                            ) + " repositories are downloaded per request")
                page += 1
                PARAMS['page'] = page
                for repo in data_repos:
                    if (
                        (not not_archived or not repo["archived"])
                        and
                        (not not_forked or not repo["fork"])
                        and
                        (not not_disabled or not repo["disabled"])
                    ):
                        file_out.write(repo["html_url"] + "\n")
                    else:
                        print(
                            f"    - The repository '{repo['url']}' has been filtered out...")

                if len(data_repos) < page_size:
                    cont = False
            except Exception as exc:
                # Propagar el error hace que el comando termine con código
                # distinto de cero y evita procesar un inventario incompleto.
                raise RuntimeError(
                    f"Could not fetch {type} '{name}', page {page}: {exc}"
                ) from exc
