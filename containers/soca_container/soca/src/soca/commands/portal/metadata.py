from ... import base_dir
from pathlib import Path
from os import listdir
from os.path import isfile, join
from datetime import datetime
import re
import sys
from pygments import highlight
from pygments.lexers.scdoc import ScdocLexer
from pygments.formatters import HtmlFormatter
import mistune
import os


# from cffconvert import Citation
# from cffconvert.cli import cli as cff2bibcli

class Metadata(object):

    def __init__(self, repo_metadata_dir, repo_metadata, embedded=False):
        self.repo_metadata_dir = os.path.abspath(repo_metadata_dir)
        self.md = repo_metadata
        self.base = 'https://github.com/oeg-upm/soca/tree/main/src/soca/assets' if embedded else ''
        
    


######################################################
# auxs
    #agrupacion de tipos de requirements
    def group_requirement_files(self, reqs):
        if not reqs:
            return None

        grouped = {}

        for r in reqs:
            if not isinstance(r, dict):
                continue

            source = r.get("source")
            if not source:
                continue

            filename = source.split("/")[-1].lower()

            if "requirements" in filename:
                key = "Source requirements.txt"
            elif filename == "pyproject.toml":
                key = "Source Poetry"
            elif filename == "codemeta.json":
                key = "Source codemeta"
            elif filename == "readme.md":
                key = "Source README"
            else:
                continue

            #  dict para deduplicar por source
            grouped.setdefault(key, {})[source] = r

        # convertir a lista final
        grouped = {k: list(v.values()) for k, v in grouped.items()}

        return grouped if grouped else None



    # agrupacion de self.docker por tipos de archivos
    def group_build_files(self, docker):

        if not docker:
            return None

        grouped = {
            "Dockerfiles": [],
            "Docker Compose files": [],
            "Poetry files": []
        }

        for url in docker:
            
            if not url or not isinstance(url, str):
                continue
            name = url.lower().split("/")[-1]

            if name == "dockerfile":
                grouped["Dockerfiles"].append(url)

            elif "docker-compose" in name:
                grouped["Docker Compose files"].append(url)

            elif name == "pyproject.toml":
                grouped["Poetry files"].append(url)

        # quitar categorías vacías
        grouped = {k: v for k, v in grouped.items() if v}

        return grouped if grouped else None


    # convertir raw url a github url
    def raw_to_github_url(self, url: str) -> str:
        if "raw.githubusercontent.com" not in url:
            return url  # ya es normal

        parts = url.split("/")

        # raw.githubusercontent.com/{owner}/{repo}/{branch}/path...
        owner = parts[3]
        repo = parts[4]
        branch = parts[5]
        path = "/".join(parts[6:])

        return f"https://github.com/{owner}/{repo}/blob/{branch}/{path}"


    # funcion para que los archivos de "docker" se vean como containers->dockefile
    def get_repo_relative_path(self, url: str) -> str:
        parts = url.split("/")

        # estructura raw github:
        # https://raw.githubusercontent.com/{owner}/{repo}/{branch}/...
        
        if len(parts) < 7:
            return url  # fallback

        path_parts = parts[6:]  # todo lo que va después de branch

        if not path_parts:
            return ""

        # si está en raíz → solo nombre
        if len(path_parts) == 1:
            return path_parts[0]

        return " → ".join(path_parts)


    # parseo de cff a bibtex
    def cff_to_bibtex(self, cff_text):
        from cffconvert import Citation

        try:
            citation = Citation(cffstr=cff_text)
            return citation.as_bibtex()
        except Exception:
            return None



    # creacion de boton para copiar bibtex


    def copy_button(self, text, label):
        import html
        import json
        if not text:
            return ""
        safe_html  = html.escape(text)
        safe_js = json.dumps(text)
        return f"""
            <div style="margin-bottom:10px;">
                <b style="font-size:0.9em;">{label}</b>
            </div>

            <div style="position:relative;">
                <button onclick='navigator.clipboard.writeText({safe_js})'
                    style="position:absolute; top:5px; right:5px;">
                    Copy
                </button>

                <pre style="
                    background:#f7f7f7;
                    padding:10px;
                    border-radius:6px;
                    font-size:0.85em;
                    overflow:auto;
                    max-height:250px;
                    white-space:pre;
                ">
        {safe_html}
                </pre>
            </div>
            """

    
    #parseador de bibtex para estructurar en html
    def parse_bibtex(self, bibtex):
        import bibtexparser

        try:
            bib_database = bibtexparser.loads(bibtex)
            entry = bib_database.entries[0] if bib_database.entries else {}

            return entry  # 🔥 TODO

        except Exception:
            return {}


        
        
    
    def parse_cff(self, cff_text):

        import yaml

        try:
        # si ya es dict no lo parsees
            if isinstance(cff_text, dict):
               parsed = cff_text
            else:
             parsed = yaml.safe_load(cff_text)
        except Exception:
            return None
        
        # TITLE
        title = parsed.get("title")

        # DOI
        doi = parsed.get("doi")
        if not doi:
            identifiers = parsed.get("identifiers", [])
            for i in identifiers:
                if i.get("type") == "doi":
                    doi = i.get("value")
                    break

        if doi and not str(doi).startswith("http"):
            doi = f"https://doi.org/{doi}"

        # AUTHORS
        authors = parsed.get("authors", [])
        authors_str = ", ".join([
            f"{a.get('given-names','')} {a.get('family-names','')}".strip()
            for a in authors
        ]) if authors else None

        # EXTRAS
        abstract = parsed.get("abstract")
        version = parsed.get("version")
        license = parsed.get("license")
        keywords = parsed.get("keywords", [])
        date_released = parsed.get("date-released")
        repo_code = parsed.get("repository-code")
        url = parsed.get("url")

        return {
            "title": title,
            "authors": authors_str,
            "doi": doi,
            "abstract": abstract,
            "version": version,
            "license": license,
            "keywords": keywords,
            "date": date_released,
            "repo_code": repo_code,
            "url": url
        }
    
    
    # Assets ####################################################
    def logo(self):
        
        # import time
        # print(self.md ,"\n", self.repo_metadata_dir,"\n", flush=True )
        # time.sleep(10)
        
        logo = safe_dic(
            safe_dic(safe_dic(safe_list(self.md, 'logo'), 0), 'result'), 'value')
        # if logo:
        # if str(logo).startswith('https://github'):
        # logo = logo.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        return logo if logo else f"{self.base}img/github-default.svg"

    def html_repo_type(self):
        repo_type = self.repo_type()
        if not repo_type:
            return ''
        if repo_type == 'web':
            return f'<img src="{self.base}repo_icons/web.png" {self.add_tooltip("left", "Website")} alt="repo-type" class="repo-type">'
        elif repo_type == 'ontology':
            # ontologies = safe_dic(safe_dic(self.md,'ontologies'),'excerpt')
            ontologies = safe_dic(self.md, 'ontologies')
            if ontologies:
                onto_list = '\n'.join(list(dict.fromkeys(
                    [f'* <{safe_dic(safe_dic(x, "result"), "value")}>' for x in ontologies if
                    'http' in safe_dic(safe_dic(x, "result"), "value")])))
                # onto_list = '\n'.join([ f'* <{safe_dic(x,"file_url")}>' for x in ontologies])
            return self.icon_wrapper(
                icon_html=f'<img src="{self.base}repo_icons/ontology.png" {self.add_tooltip("left", "Ontology")} alt="repo-type" class="repo-type" style="height: 1.3rem;">',
                modal_html=self.modal(
                    title='Ontologies',
                    body=onto_list
                ),
                other_field='class="m_ontology"'
            )
        return f'<div class="grey-color-svg" style="display:flex;" {self.add_tooltip("left", f"Python {repo_type}")}><img src="{self.base}language_icons/python.svg" alt="repo-type" class="repo-type"></div>'

    def icon_star(self):
        return f"{self.base}repo_icons/star.png"

    def icon_releases(self):
        return f"{self.base}repo_icons/releases.png"

    def html_description(self):
        return f'<span>{mistune.html(self.description())}</span>'

    def html_languages(self):

        languages = self.languages()

        if not languages:
            return ''

        language_icons_dir = Path(base_dir, 'assets', 'language_icons')
        supported_languages = [str(f).removesuffix('.svg').lower() for f in listdir(language_icons_dir) if
                               isfile(join(language_icons_dir, f))]

        html = ''

        for lang in languages:
            if lang in supported_languages:
                html += f"""<img src="{self.base}language_icons/{lang}.svg" 
                                alt="{lang}" class="repo-icon grey-color-svg"
                                data-toggle="tooltip" data-placement="bottom" title="{lang.capitalize()}">"""
        return html

    def copy_btn(self):
        return f"""<button class="copy-btn" 
                   value="{self.repo_url()}" 
                   style="background:url('{self.base}repo_icons/copy.svg')transparent;background-repeat:no-repeat;background-size:auto;"
                   data-toggle="tooltip" data-placement="right" title="Copy card as embbeded HTML">
                   </button>"""

    def html_license(self, license_input):
        if safe_dic(license_input, "url"):
            html = """
            <h3 class="ref-name"></h3>
            <span class="ref-description-aux">
                <h4>Description:</h4>
                <p class="ref-description" style="text-align: justify;">Loading...</p>

                <h4>Permissions:</h4>
                <div class="ref-permissions"><ul><li>Loading...</li></ul></div>

                <h4>Conditions:</h4>
                <div class="ref-conditions"><ul><li>Loading...</li></ul></div>

                <h4>Limitations:</h4>
                <div class="ref-limitations"><ul><li>Loading...</li></ul></div>
            </span>
            """
        else:
            html = f"""
            <h3 class="ref-name">{safe_dic(license_input, "name")}</h3>

            <h4>Description:</h4>
            <p class="ref-description">There is not an available description.</p>
            """
        return html

    def html_repo_icons(self):
    
        #debugging de nombre del repo para prints
        #raw_url = safe_dic(safe_dic(safe_list(safe_dic(self.md, 'readme_url'), 0), 'result'), 'value')
        #parts = raw_url.split("/")
        #repo = parts[4]
        
        
        

        html = ''

        readme_url = self.readme()
        if readme_url:
            html += self.icon_wrapper(
                icon_html=f"""<a href="{readme_url}" target="_blank" class="repo-icon">
                            <img src="{self.base}repo_icons/readme.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', 'Readme')}>
                        </a>""")

        license = self.license()
        if license:
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/license.png" 
                            class="repo-icon"
                            {self.add_tooltip('bottom', f'License: {safe_dic(license, "name")}')}>
                            """,
                modal_html=self.modal(
                    title='License',
                    body=self.html_license(license),
                    markdown_translation=False),
                other_field=f'data-url="{safe_dic(license, "url")}"',
                extra_class='ref-license'
            )

        notebook = self.notebook()
        if notebook:
            mk_list = "\n".join([f'* <{n}>' for n in notebook])
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/notebook.png" 
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Notebook')}>""",

                modal_html=self.modal(
                    title='Notebook',
                    body=mk_list))

        
        
        

        
        # docker antiguo
        '''
        docker = self.docker()
        
        if docker:
            

            mk_list = "\n".join([f'* <{d}>' for d in docker])
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/docker.png" 
                        class="repo-icon" 
                        {self.add_tooltip('bottom', "Docker")}>""",

                modal_html=self.modal(
                    title='Docker',
                    body=mk_list))
        
        
        '''
        #docker propio, saca la parte docker de somef y la agrupa por tipos de archivos importantes
        docker = self.docker()
        grouped = self.group_build_files(docker)


        if grouped:
                
                body = "<div style='max-height:300px; overflow:auto;'>"

                for category, urls in grouped.items():

                    body += f"<b>{category}</b><br>"

                    for url in urls:
                        display = self.get_repo_relative_path(url)
                        github_url = self.raw_to_github_url(url)
                        body += f"""
                        • <a href="{github_url}" target="_blank">{display}</a><br>
                        """

                    body += "<br>"

                body += "</div>"
                
                html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/docker.png" 
                                class="repo-icon" 
                                {self.add_tooltip('bottom', "Docker / Build Files")}>""",
                modal_html=self.modal(
                    title='Docker / Build Files',
                    body=body,
                    markdown_translation=False
    )
)
        
        
        
            
            
            
            
            
        papers = self.paper()
        if papers:
            for paper in papers:
                html += self.icon_wrapper(
                    icon_html=f"""<a href="{paper.link_paper}" target="_blank" class="repo-icon">
                                <img src="{self.base}repo_icons/paper.png" 
                                class="repo-icon" 
                                {self.add_tooltip('bottom', paper.title_paper)}>
                        </a>""")
    
    
    
    

        
        '''
    
        # TODO check ScdocLexer
        citations = self.citations()
        if citations:
            citation = "No Citation Indicated"
            formatter = HtmlFormatter(
                linenos=False, full=True, style='friendly')
            # TODO once fixed turn to if, elif, else  so that it prioritises CFF (converted to bibtex format)
            if 'bibtex' in citations:
                citation = safe_dic(citations, "bibtex")
            elif 'cff' in citations:
                citation = safe_dic(citations, "cff")
                if citation:
                    citation.replace("`", "")
                # try:
                #     cite = Citation(cffstr=safe_dic(citations,"cff"))
                #     citation = cite.as_bibtex()
                # except:
            else:
                try:
                    citation = citations['citation'][0]
                    # citation = safe_list(safe_dic(citations,citation),0)
                except Exception as e:
                    print(str(e))
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/citation.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', f"Citation")}>""",
                modal_html=self.modal(
                    title='Citation',
                    body=f'<div style="font-family: monospace;">{highlight(citation, ScdocLexer(), formatter)}</div>',
                    markdown_translation=False,
                    extra_html=f"""
                        <button 
                            class="copy-citation-btn" 
                            value="{self.repo_url()}" 
                            style="background:url('repo_icons/copy.svg')transparent;background-repeat:no-repeat;background-size:auto;" 
                            data-toggle="tooltip" 
                            data-placement="right" 
                            data-original-title="Copy citation">
                        </button>
                        """))
        
        
        '''
        
        # citations propio
        citations = self.citations()

        
        if citations:
            
            citation = None
            #formateador  para highlight y cuadrar
            formatter = HtmlFormatter(linenos=False, full=True, style='friendly')
            body = ""
            

            #  1º ver si hay bibtex y añadirlo al body
            if 'bibtex' in citations and citations['bibtex']:
                
                
                
                bib = safe_dic(citations, "bibtex")          
                parsed_bib = self.parse_bibtex(bib)
                bib_clean = ""
                bib_button = self.copy_button(bib, "BibTeX")
                
                for key, value in parsed_bib.items():
                    
                    if not value:
                        continue

                    # ignorar campos internos
                    if key in ["ID", "ENTRYTYPE"]:
                        continue

                    # label bonito automático
                    label = key.capitalize()

                    # links
                    if key in ["doi", "url"]:
                        if not str(value).startswith("http") and key == "doi":
                            value = f"https://doi.org/{value}"
                        value = f"<a href='{value}' target='_blank'>{value}</a>"

                    # autores más bonitos
                    if key == "author":
                        value = value.replace(" and ", ", ")

                    bib_clean += f"<b>{label}:</b> {value}<br>"
                        

                body = f"""
                <div style="margin-bottom:15px;">
                    {bib_button}
                </div>
                
                <div style="margin-bottom:15px; max-height:350px; overflow:auto;">
                    <b style="font-size:1.1em;">Source by BibTeX</b><br><br>
                    <div style="font-size:0.9em;">
                        {bib_clean}
                    </div>
                </div>
                """

            # 2º citation
            elif 'cff' in citations and citations['cff']:

                citation = safe_dic(citations, "cff")
                parsed = self.parse_cff(citation)
                import yaml

                if isinstance(citation, dict):
                    citation = yaml.dump(citation)
                    
                bibtex_generated = self.cff_to_bibtex(citation)
                bib_button = self.copy_button(bibtex_generated, "BibTeX")
                
                if parsed:

                    body = f"""
                    <div style="margin-bottom:15px;">
                        {bib_button}
                    </div>
                    
                    <div style="margin-bottom:15px; max-height:350px; overflow:auto;">
                        <b style="font-size:1.1em;">Source by .cff</b><br><br>

                        {f"<b>Title:</b> {parsed['title']}<br>" if parsed['title'] else ""}
                        {f"<b>Authors:</b> {parsed['authors']}<br>" if parsed['authors'] else ""}
                        {f"<b>DOI:</b> <a href='{parsed['doi']}' target='_blank'>{parsed['doi']}</a><br>" if parsed['doi'] else ""}
                        {f"<b>Version:</b> {parsed['version']}<br>" if parsed['version'] else ""}
                        {f"<b>Released:</b> {parsed['date']}<br>" if parsed['date'] else ""}
                        {f"<b>License:</b> {parsed['license']}<br>" if parsed['license'] else ""}
                        {f"<b>Code:</b> <a href='{parsed['repo_code']}' target='_blank'>{parsed['repo_code']}</a><br>" if parsed['repo_code'] else ""}
                        {f"<b>Project:</b> <a href='{parsed['url']}' target='_blank'>{parsed['url']}</a><br>" if parsed['url'] else ""}
                    """

                    # keywords
                    if parsed["keywords"]:
                        keywords_str = ", ".join(parsed["keywords"][:6])
                        body += f"<b>Keywords:</b> {keywords_str}<br>"

                    # abstract bonito
                    if parsed["abstract"]:
                        body += f"""
                        <br>
                        <b>Abstract:</b>
                        <details>
                            <summary style="cursor:pointer;">Show abstract</summary>
                            <div style="
                                font-size:0.9em;
                                color:#444;
                                text-align: justify;
                                margin-top:5px;
                                padding:8px;
                                background:#f7f7f7;
                                border-radius:6px;
                                max-height:200px;
                                overflow:auto;
                            ">
                                {parsed['abstract']}
                            </div>
                        </details>
                        """

                    body += "</div>"
        
            # 3º si hay texto de cita añadirlo
            elif 'citation' in citations and citations['citation']:
                

                citation = safe_list(safe_dic(citations, 'citation'), 0)
                body += f"""
                <b style="font-size:1.1em;">Source by documentation</b><br><br>
                <div style="
                    font-size:0.95em;
                    line-height:1.5;
                    background:#f7f7f7;
                    padding:10px;
                    border-radius:6px;
                ">
                    {citation}
                </div>
                """

            # si no texto
            elif not body or body == "":

            #else:
                
                body = "<i>No citation available</i>"

            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/citation.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', "Citation")}>""",
                modal_html=self.modal(
                    title='Citation',
                    body=body,
                    markdown_translation=False
                )
            )

        
            
        '''
        identifier = self.identifier()
        if identifier:
            html += self.icon_wrapper(
                icon_html=f"""<a href="{identifier}" target="_blank" class="repo-icon">
                            <img src="{self.base}repo_icons/doi.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', f"DOI: {identifier}")}>
                    </a>""")
        '''
        
        # modificado para que no se construyan rutas relativas de localhost
        identifier = self.identifier()
        
        if identifier:
            doi_url = identifier

            # si no viene como URL → construirla
            if not doi_url.startswith("http"):
                doi_url = f"https://doi.org/{doi_url}"

            html += self.icon_wrapper(
                icon_html=f"""<a href="{doi_url}" target="_blank" class="repo-icon">
                                <img src="{self.base}repo_icons/doi.png" 
                                class="repo-icon" 
                                {self.add_tooltip('bottom', f"DOI: {identifier}")}>
                        </a>"""
            )
                


        status = self.status()
        if status:
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/status.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', 'Status')}>
                            """,

                modal_html=self.modal(
                    title='Status',
                    body='### Description  \n' +
                    safe_dic(safe_dic(safe_list(status, 0),
                             'result'), 'description')
                         + '\n #### More information  \n' + f'<{safe_dic(safe_dic(safe_list(status, 0), "result"), "value")}>'))




        '''
        installation = self.installation()
        if installation:
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/installation.png" 
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Installation')}>""",

                modal_html=self.modal(
                    title='Installation',
                    body=f'{installation}'))
        '''
        installation = self.installation()
        if installation:

            md_text = ""
            source = installation[0].get("source")
            if source:
                filename = source.split("/")[-1]
                md_text += f"**Source {filename}:** \n\n"
            for item in installation:
                # header de la instalacion
                header = safe_dic(safe_dic(item, "result"), "original_header")
                # contenido del header
                text = safe_dic(safe_dic(item, "result"), "value")

                if header:
                    md_text += f"### {header}\n\n"

                if text:
                    md_text += text.replace("\n", "  \n") + "\n\n"
                    
                md_text += "---\n\n"
                
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/installation.png" 
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Installation')}>""",

                modal_html=self.modal(
                    title='Installation',
                    body=md_text,                
                    markdown_translation=True     
                )
            )


        '''
        requirements = self.requirements()
        if requirements:
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/requirements.png"  
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Requirements')}>""",

                modal_html=self.modal(
                    title='Requirements',
                    body=requirements))
        '''
        
        # propio agrupando requirements
        raw_requirements = self.requirements()
        
        grouped_reqs = self.group_requirement_files(raw_requirements)
        if grouped_reqs:
            body = """
            <div style="
                max-height:300px;
                overflow:auto;
                display:block;
            ">
            """

            for filetype, items in grouped_reqs.items():

                body += f"<b>{filetype}</b><br>"

                for r in items:

                    source = r.get("source")
                    value = safe_dic(safe_dic(r, "result"), "value")

                    filename = source.split("/")[-1].lower() if source else ""

                    #  README mostrar contenido
                    if "readme.md" in filename and value:

                        html_md = mistune.html(value).replace("<p>", "").replace("</p>", "")
                        body += f"""
                        <div style="
                                background:#f7f7f7;
                                padding:10px;
                                border-radius:6px;
                                font-size:0.9em;
                                margin-bottom:10px;
                            ">
                            {html_md}
                        </div>
                        """

                    #  resto link normal
                    else:
                        display = self.get_repo_relative_path(source)
                        github_url = self.raw_to_github_url(source)

                        body += f"""
                        <a href="{github_url}" target="_blank">{display}</a><br>
                        """

                body += "<br>"
                body += "</div>"
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/requirements.png"  
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Requirements')}>""",
                modal_html=self.modal(
                    title='Requirements',
                    body=body,
                    markdown_translation=False
                )
            )
        


                
                
                
                
        usage = self.usage()
        if usage:
            has_i4p = safe_dic(safe_dic(self.md, 'inspect4py'), 'run') # TODO:  inspect4py & run are not keys in the new Results class
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/usage.png"  
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Usage')}>""",
                modal_html=self.modal(
                    title='How to use it' if has_i4p and '### How to use it' not in usage else 'Usage',
                    body=usage))

        help = self.help()
        if help:
            html += self.icon_wrapper(
                icon_html=f"""<img src="{self.base}repo_icons/help.png"  
                        class="repo-icon" 
                        {self.add_tooltip('bottom', 'Help')}>""",

                modal_html=self.modal(
                    title='Help',
                    body=help))

        hasDocumentation = self.hasDocumentation()
        if hasDocumentation:
            if len(hasDocumentation) > 1:
                # mk_list = "\n".join([f'* <{d}>' if ('http' in d and not ' ' in d) else f'* {d}' for d in hasDocumentation])

                mk_list = "\n".join([
                    f'* <{safe_dic(safe_dic(d, "result"), "value")}>' if (
                        self._is_valid_url(safe_dic(safe_dic(d, "result"), "value")))
                    else f'* {safe_dic(safe_dic(d, "result"), "value")}' for d in hasDocumentation
                ])

                html += self.icon_wrapper(
                    icon_html=f"""<img src="{self.base}repo_icons/documentation.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', "Documentation")}>""",

                    modal_html=self.modal(
                        title='Documentation',
                        body=mk_list))
            else:
                doc = safe_dic(
                    safe_dic(safe_list(hasDocumentation, 0), 'result'), 'value')
                if self._is_valid_url(doc):
                    html += self.icon_wrapper(
                        icon_html=f"""<a href="{doc}" target="_blank" class="repo-icon">
                                                    <img src="{self.base}repo_icons/documentation.png" 
                                                    class="repo-icon" 
                                                    {self.add_tooltip('bottom', 'Documentation')}>
                                                </a>""")
                else:
                    html += self.icon_wrapper(
                        icon_html=f"""<img src="{self.base}repo_icons/documentation.png" 
                                class="repo-icon" 
                                {self.add_tooltip('bottom', 'Documentation')}>""",

                        modal_html=self.modal(
                            title='Documentation',
                            body=f'{doc}'))

        acknowledgement = self.acknowledgement()
        if acknowledgement:
            html += self.icon_wrapper(

                icon_html=f"""<img src="{self.base}repo_icons/acknowledgement.png" 
                        class="repo-icon" 
                        {self.add_tooltip('bottom', f"Acknowledgement")}>""",

                modal_html=self.modal(
                    title='Acknowledgement',
                    body=f'{acknowledgement}'))

        downloadUrl = self.downloadUrl()
        if downloadUrl:
            html += self.icon_wrapper(

                icon_html=f"""<a href="{downloadUrl}" target="_blank" class="repo-icon">
                            <img src="{self.base}repo_icons/download.png" 
                            class="repo-icon" 
                            {self.add_tooltip('bottom', 'Download')}>
                        </a>"""
            )

        return html

    def _is_valid_url(self, url):
        """Private function to check if a string is a valid URL."""
        import re

        # Regular expression to match a valid URL
        url_regex = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

        # Check if the input string matches the URL regex
        return bool(url_regex.match(url))

    # HTML helper ##################################################

    def add_tooltip(self, placement, tooltip_text):
        """Supported placements: ['bottom', 'up', 'right', 'left']"""
        return f'''data-toggle="tooltip" data-placement="{placement}" title="{tooltip_text}" alt="{tooltip_text}"'''



    def icon_wrapper(self, icon_html, modal_html=None, other_field=None, extra_class=None):
         return f"""<div {other_field if other_field else ''} class="icon-wrapper{' ' + extra_class if extra_class else ''}">
                        <div class="icon">{icon_html}</div>
                        {modal_html if modal_html else ''}
                     </div>"""



    def modal(self, title, body, markdown_translation=True, extra_html=''):

        if markdown_translation:
            body = mistune.html(body)

        return f"""<div class="modal">
                        <div class="modal-content">
                            <span class="close">&times;</span>
                            <span style="display:flex;">
                                <h2 style="margin-bottom: 1rem;">{title}</h2>
                                {extra_html}
                            </span>
                            <div style="margin-bottom: 1rem; overflow: auto;">{body}</div>
                        </div>
                    </div>"""

    # Metadata ##################################################
    def last_release(self):
        if self.n_releases() != 0:
            if not safe_dic(safe_dic(safe_list(self.releases(), 0), 'result'), 'name'):
                if (tag := safe_dic(safe_dic(safe_list(self.releases(), 0), 'result'), 'tag')):
                    return tag
                else:
                    return "Missing Descriptors"
            return safe_dic(safe_dic(safe_list(self.releases(), 0), 'result'), 'name')
        else:
            return ''
        # return safe_dic(safe_dic(safe_list(self.releases(),0),'result'),'name') if self.n_releases() != 0 else ''

    # TODO
    def repo_type(self):

        ######################

        if "type" in self.md.keys():
            return self.md["type"]

        # web and ontology
        ######################

        if (safe_dic(self.md, 'ontologies') is not None):
            return 'ontology'

        langs = self.languages()
        is_web = (langs and 'html' in langs)

        if langs:
            for lang in langs:
                if lang not in ['html', 'css', 'javascript']:
                    is_web = False
                # if lang not in ['html','css','javascript']:
                # is_ontology = False
        if is_web:
            return 'web'

        return None

    def usage(self):
        usage_list = safe_dic(self.md, 'usage')
        usage = None
        if usage_list:
            usage = ''
            for u in usage_list:
                usage += u['result']['value'] + '\n'
        
        run_list = safe_dic(safe_dic(self.md, 'inspect4py'), 'run') # TODO:  inspect4py & run are not keys in the new Results class
        if run_list:
            if isinstance(run_list, list):
                run = '\n'.join(
                    [f'* {str(x).replace(self.repo_metadata_dir, "")}' for x in run_list])
            else:
                run = run_list.replace(self.repo_metadata_dir, "")
            run_md = '---\n  ### How to use it  \n' + run if usage else run

        else:
            run_md = ''

        usage = usage if usage else ''

        return usage + run_md if usage or run_md else None

    # TODO cannot find correct implementation
    def help(self):
        support = safe_dic(safe_dic(
            safe_list(safe_dic(self.md, 'support'), 0), 'result'), 'value')
        faq = safe_dic(
            safe_dic(safe_list(safe_dic(self.md, 'faq'), 0), 'result'), 'value')
        supportChannels = safe_dic(safe_dic(
            safe_list(safe_dic(self.md, 'supportChannels'), 0), 'result'), 'value')

        support_md = ('### Support  \n' + support) if support else ''
        faq_md = ('### FAQ  \n' + faq) if faq else ''
        supportChannels_md = ('### Support Channels  \n' +
                              supportChannels) if supportChannels else ''

        return support_md + faq_md + supportChannels_md if support or faq or supportChannels else None

    def recently_updated(self):
        # TODO: Retreive days_threshold from properties file
        hex_states = [
            {'hex': '#6da862', 'days_threshold': 30},
            {'hex': '#a88d62', 'days_threshold': 90},
            {'hex': '#a86262', 'days_threshold': sys.maxsize}
        ]

        delta = self.last_update_days()

        state_updated = ''
        for state in hex_states:
            if delta < state['days_threshold']:
                state_updated = state['hex']
                break

        return f"""<div class="recently-updated" style="background-color: {state_updated};"
                   data-toggle="tooltip" data-placement="right" 
                   title="Last updated on: {self.last_update().strftime('%d-%m-%Y')}">
                   </div>"""

    def identifier(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'identifier'), 0), 'result'), 'value')

    def status(self):
        return safe_dic(self.md, 'repository_status')

    def acknowledgement(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'acknowledgement'), 0), 'result'), 'value')

    def hasDocumentation(self):
        docList = safe_dic(self.md, 'documentation')
        return docList if docList else None


    def requirements(self):
        reqs = safe_dic(self.md, 'requirements')
        if not reqs:
            return None
        '''
        for d in reqs:
            source = d.get("source")
            if source == "https://raw.githubusercontent.com/oeg-upm/rsfc/main/README.md":
                print("ENCONTRADO EN README:")
                import json
                print(json.dumps(reqs, indent=4, ensure_ascii=False))
        '''        
 
        return reqs

       
    def installation(self):
        inst = safe_dic(self.md, 'installation')
        if not inst:
            return None
        return inst

    
    '''
    def installation(self):
        inst = safe_dic(self.md, 'installation')
        import json

        if not inst:
            return None

        values = []

        for d in inst:
            source = d.get("source")

            if source == "https://raw.githubusercontent.com/oeg-upm/rsfc/main/README.md":
                print("ENCONTRADO EN README:")
                print(json.dumps(inst, indent=4, ensure_ascii=False))


            values.append(safe_dic(safe_dic(d, 'result'), 'value'))

        return "\n".join(values)
    '''
    
    '''
    def docker(self):

        hasBuildFileList = safe_dic(self.md, 'has_build_file')
        if not hasBuildFileList:
            return None
    
        return [safe_dic(safe_dic(d, 'result'), 'value') for d in hasBuildFileList]
    '''
    
    # implementación para sacar los requirements del build file y que no haya requirements.txt
    # esto para que se filtre bien todo en el portal
    def docker(self):

        hasBuildFileList = safe_dic(self.md, 'has_build_file')

        if not hasBuildFileList:
            return None

        urls = [safe_dic(safe_dic(d, 'result'), 'value') for d in hasBuildFileList]

        grouped = self.group_build_files(urls)

        if not grouped:
            return None

        # devolver SOLO los archivos válidos
        filtered_urls = []
        for v in grouped.values():
            filtered_urls.extend(v)

        return filtered_urls
    
    
    

    def downloadUrl(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'download_url'), 0), 'result'), 'value') \
            if self.n_releases() > 0 else None

    # TODO change name to something more self explanatory
    def notebook(self):
        exe_l = safe_dic(self.md, 'executable_example')
        exe_l = exe_l if exe_l else []
        exe = [x['result']['value'] for x in exe_l]
        return exe if len(exe) > 0 else None

    '''
    def readme(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'readme_url'), 0), 'result'), 'value')
    '''
    
    
    # nuevo readme para leer del readme desde gitub y no raw
    def readme(self):
        raw_url = safe_dic(safe_dic(safe_list(safe_dic(self.md, 'readme_url'), 0), 'result'), 'value')
        
        if not raw_url:
            return None

        if "raw.githubusercontent.com" in raw_url:
            parts = raw_url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[5]
            filename = parts[-1]
            return f"https://github.com/{user}/{repo}/tree/{branch}/{filename}"

        return raw_url

    def languages(self):
        langs = safe_dic(self.md, 'programming_languages')
        if not langs:
            return None
        return [str(safe_dic(safe_dic(lang, 'result'), 'value')).lower() for lang in langs]

    def repo_url(self):
        return safe_dic(safe_list(safe_dic(safe_dic(self.md, 'code_repository'), 0), 'result'), 'value')

    def title(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'name'), 0), 'result'), 'value')

    # TODO find new
    def description(self):

        all_descriptions = safe_dic(self.md, 'description')

        description = None
        if all_descriptions:
            for d in all_descriptions:
                if safe_dic(d, 'technique') == 'GitHub API':
                    description = safe_dic(safe_dic(d, 'result'), 'value')
                    break

        if not description:
            description = safe_dic(
                safe_dic(safe_list(all_descriptions, 0), 'result'), 'value')
            if not description:
                description = 'No description available yet.'

        return description

    def license(self):
        license = safe_dic(
            safe_list(safe_dic(self.md, 'license'), 0), 'result')
        if (typ := safe_dic(license, "type")) and ((typ == "File_dump") or (typ == "Text_excerpt")):
            self._find_license_name(license)
            return license
        else:
            return license

    def _find_license_name(self, license):
        find_name = safe_dic(license, "value")
        if 'Apache' in find_name:
            license['name'] = 'Apache License 2.0'
            license['url'] = 'https://api.github.com/licenses/apache-2.0'
        elif 'MIT' in find_name:
            license['name'] = 'MIT License'
            license['url'] = 'https://api.github.com/licenses/MIT'
        elif 'GPL' in find_name:
            license['name'] = 'GNU General Public License v3.0'
            license['url'] = 'https://api.github.com/licenses/gpl-3.0'
        else:
            license['name'] = 'Other'

    def last_update(self):
        result = safe_dic(
            safe_list(safe_dic(self.md, 'date_updated'), 0), 'result')
        date_modified_str = of_correctType(result, 'Date')[:-1]
        date_modified = datetime.strptime(
            date_modified_str, '%Y-%m-%dT%H:%M:%S')
        return date_modified

    def last_update_days(self):
        date_of_extraction_str = safe_dic(
            safe_dic(self.md, 'somef_provenance'), 'date')[:]
        date_of_extraction = datetime.strptime(
            date_of_extraction_str, '%Y-%m-%d %H:%M:%S')
        last_update = self.last_update()
        return (date_of_extraction - last_update).days

    def stars(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'stargazers_count'), 0), 'result'), 'value')

    def n_releases(self):
        rel = safe_dic(self.md, 'releases')
        return len(rel) if rel is not None else 0

    def releases(self):
        return safe_dic(self.md, 'releases')

    def url_releases(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'download_url'), 0), 'result'), 'value')

    def url_stars(self):
        return self.repo_url() + '/stargazers'

    def owner(self):
        return safe_dic(safe_dic(safe_list(safe_dic(self.md, 'owner'), 0), 'result'), 'value')

    # IMPORTANT !!!!! ASSUMES only 1 CFF per repo
    # USE SOMEF as example it lists SOMEF CFF then WIDOCO then SOMEF then CAPTUM
    def citations(self):
        all_citations = safe_dic(self.md, 'citation')

        if not all_citations:
            return None

        citations = {'citation': []}

        for c in all_citations:
            try:
                type = ""
                type = c['result']['format']
            except:
                try:
                    if c['result']['type'] == 'Text_excerpt':
                        citations['citation'].append(c['result']['value'])
                except:
                    continue
            match type:
                case 'cff':
                    citations['cff'] = c['result']['value']
                case 'bibtex':
                    citations['bibtex'] = c['result']['value']
                case _:
                    continue
        # return citations if len(citations) > 0 else None
        test = len(citations)
        
        '''COMENTADO POR PROPIO'''
        '''return citations if bool(citations) else None '''

        has_content = (
            citations.get("bibtex") is not None or
            citations.get("cff") is not None or
            (citations.get("citation") and len(citations.get("citation")) > 0)
        )

        return citations if has_content else None
    # Originally citations Took the ver8 somef "regular expression" output and would create a list of excerpts

    def paper(self):
        citations = safe_dic(self.citations(), 'citation')
        p = []
        if citations:
            for cita in citations:

                c = CitationParser(cita)

                if c.link_paper and 'zenodo' not in c.link_paper:
                    p.append(c)

        return p if len(p) > 0 else None


# Aux ##########################################################

def safe_dic(dic, key):
    try:
        return dic[key]
    except:
        return None


def safe_list(list, i):
    try:
        return list[i]
    except:
        return None


def of_correctType(result, ofType):
    if safe_dic(result, 'type') == ofType:
        return safe_dic(result, 'value')
    else:
        raise Exception("not of correct %s type" % ofType)


class CitationParser(object):

    def __init__(self, citation) -> None:
        self.link_paper = re.search('url[ ]*=[ ]*{(.*)}', citation)
        if self.link_paper:
            self.link_paper = self.link_paper.group(1)

        self.doi_paper = re.search('doi[ ]*=[ ]*{(.*)}', citation)
        if self.doi_paper:
            self.doi_paper = self.doi_paper.group(1)

        self.title_paper = re.search('title[ ]*=[ "]*{(.*)}', citation)
        if self.title_paper:
            self.title_paper = self.title_paper.group(1)

        if self.doi_paper and 'http' not in self.doi_paper:
            self.doi_paper = 'https://www.doi.org/' + self.doi_paper
            self.link_paper = self.doi_paper
