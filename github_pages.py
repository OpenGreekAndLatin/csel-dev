from lxml import etree
import os
from glob import glob
from pickle import load
import re
from collections import defaultdict
import json
import argparse


class CreatePage:

    def __init__(self, orig, dest, out="html", head="", foot="", url_base="", hook_results=""):
        """

        :param orig: The /data folder for the local CapiTainS repository
        :type orig: str
        :param dest: the destination to save the .txt file with the markdown
        :type dest: str
        :param hook_results: the pickled dictionary where the HookTest results for this repository are located
        :type hook_results: str
        """
        self.orig = orig
        self.dest = dest
        if out == "html":
            self.bold_start = "<strong>"
            self.bold_end = "</strong>"
            self.it_start = "<em>"
            self.it_end = "</em>"
        elif out == "markdown":
            self.bold_start = self.bold_end = "**"
            self.it_start = self.it_end = "*"
        with open(head) as f:
            self.head = f.read()
        with open(foot) as f:
            self.foot = f.read()
        self.url_base = url_base
        self.hook_results = {}
        total_words = 0
        try:
            if hook_results.endswith('pickle'):
                with open(hook_results, mode="rb") as f:
                    results = load(f)
            elif hook_results.endswith('json'):
                with open(hook_results) as f:
                    results = json.load(f)
            for r in results['units']:
                try:
                    self.hook_results[r['name'].split('/')[-1]] = "{:,}".format(r['words'])
                    total_words += r['words']
                except:
                    continue
        except:
            print("No results found")
            self.hook_results = {}
        self.head = re.sub(r'<strong id="word_count">[\d,]+</strong>', r'<strong id="word_count">{:,}</strong>'.format(total_words), self.head)
        self.author_words = defaultdict(int)
        self.source_words = defaultdict(int)

    def write_dict(self):
        """

        :return: the dictionary containing all the authors, works, and editions
        :rtype: {urn: {"name": str, "works": {urn (str): {"editions": [edition1 (str), edition2 (str)]}}}}
        """
        ns = {"ti": "http://chs.harvard.edu/xmlns/cts", "tei": "http://www.tei-c.org/ns/1.0"}
        authors = [x for x in glob("{}/*".format(self.orig)) if os.path.isdir(x)]
        work_dict = {}
        for author in authors:
            try:
                a_root = etree.parse("{}/__cts__.xml".format(author)).getroot()
                a_urn = a_root.xpath("/ti:textgroup", namespaces=ns)[0].get("urn").split(":")[-1]
                a_name = a_root.xpath("/ti:textgroup/ti:groupname", namespaces=ns)[0].text
                work_dict[a_urn] = {"name": "{0}{1} ({2}{3}{4}){5}".format(self.bold_start,
                                                                           a_name,
                                                                           self.it_start,
                                                                           a_urn,
                                                                           self.it_end,
                                                                           self.bold_end), "works": {}}
            except OSError:
                print("No metadata for author {}".format(os.path.basename(author)))
                continue
            works = [w for w in glob("{}/*".format(author)) if os.path.isdir(w)]
            for work in sorted(works):
                try:
                    w_root = etree.parse("{}/__cts__.xml".format(work)).getroot()
                    w_urn = w_root.xpath("/ti:work", namespaces=ns)[0].get("urn").split(":")[-1]
                    w_name = w_root.xpath("/ti:work/ti:title", namespaces=ns)[0].text
                    work_dict[a_urn]["works"][w_urn] = {"name": "{0}{1} {2}({3})".format(self.it_start, w_name, self.it_end, w_urn), "editions": []}
                except OSError:
                    print("No metadata for the work {}/{}".format(os.path.basename(author), os.path.basename(work)))
                    continue
                for edition in w_root.xpath("/ti:work/ti:edition", namespaces=ns):
                    e_urn = edition.get("urn").split(":")[-1]
                    try:
                        e_root = etree.parse("{}/{}.xml".format(work, e_urn)).getroot()
                        source_root = e_root.xpath("/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:respStmt/tei:orgName", namespaces=ns)
                    except OSError:
                        source_root = None
                    except Exception:
                        print("There was a problem with {}".format(e_urn))
                    if source_root:
                        source = source_root[0].text.split(",")[0]
                    else:
                        source_root = e_root.xpath("/tei:TEI/tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:funder", namespaces=ns)
                        try:
                            source = source_root[0].text.split(",")[0]
                        except:
                            source = "Unknown"
                    source = re.sub(r"\s+", " ", source)
                    e_name = edition.xpath("./ti:description", namespaces=ns)[0].text
                    e_url = "{}/{}/{}/{}.xml".format(self.url_base, e_urn.split(".")[0], e_urn.split(".")[1], e_urn)
                    if self.hook_results:
                        try:
                            e_words = self.hook_results['{}.xml'.format(e_urn)]
                        except KeyError as E:
                            print("Nothing found for {}".format(e_urn))
                            e_words = "0"
                        self.author_words[a_urn] += int(e_words.replace(",", ""))
                        self.source_words[source] += int(e_words.replace(",", ""))
                        if self.it_start == "*":
                            work_dict[a_urn]["works"][w_urn]["editions"].append(
                                "[{0} ({1}{2}{3})]({4}) - {5} words\nSource: {6}".format(e_name,
                                                                            self.it_start,
                                                                            e_urn,
                                                                            self.it_end,
                                                                            e_url,
                                                                            e_words,
                                                                            source))
                        else:
                            work_dict[a_urn]["works"][w_urn]["editions"].append(
                                '<a href="{4}">{0} ({1}{2}{3}) - {5} words</a><br>Source: {6}'.format(e_name,
                                                                                       self.it_start,
                                                                                       e_urn,
                                                                                       self.it_end,
                                                                                       e_url,
                                                                                       e_words,
                                                                                        source))
                    else:
                        if self.it_start == "*":
                            work_dict[a_urn]["works"][w_urn]["editions"].append("[{0} ({1}{2}{3})]({4})\nSource: {5}".format(e_name,
                                                                                                                self.it_start,
                                                                                                                e_urn,
                                                                                                                self.it_end,
                                                                                                                e_url,
                                                                                                                source))
                        else:
                            work_dict[a_urn]["works"][w_urn]["editions"].append('<a href="{4}">{0} ({1}{2}{3})</a><br>Source: {5}'.format(e_name,
                                                                                                                           self.it_start,
                                                                                                                           e_urn,
                                                                                                                           self.it_end,
                                                                                                                           e_url,
                                                                                                                            source))
        return work_dict

    def write_results(self, work_dict):
        """

        :param work_dict: the dictionary containing all the authors, works, and editions
        :type work_dict: {urn: {"name": str, "works": {urn: {"editions": [edition1, edition2]}}}}
        :return: the formatted markdown string
        :rtype: str
        """
        raise NotImplementedError("write_results is not implemented on the base class")

    def save_txt(self, results):
        """

        :param results: the formatted string created by self.write_results
        :type results: str
        """
        with open(self.dest, mode="w") as f:
            f.write(results)

    def run_all(self):
        """ A convenience function to automatically run all functions.

        """
        work_dict = self.write_dict()
        results = self.write_results(work_dict)
        self.save_txt(results)


class CreateMarkdown(CreatePage):

    def write_results(self, work_dict):
        """

        :param work_dict: the dictionary containing all the authors, works, and editions
        :type work_dict: {urn: {"name": str, "works": {urn: {"editions": [edition1, edition2]}}}}
        :return: the formatted markdown string
        :rtype: str
        """
        markdown = ''
        for a in sorted(work_dict.keys(), key=lambda x: work_dict[x]["name"].lower()):
            markdown = markdown + "+ {}** - {:,} words**\n".format(work_dict[a]["name"], self.author_words[a])
            for work in sorted(work_dict[a]["works"].keys(), key=lambda x: work_dict[a]["works"][x]["name"].lower()):
                markdown = markdown + "    + {}\n".format(work_dict[a]["works"][work]["name"])
                for edition in work_dict[a]["works"][work]["editions"]:
                    markdown = markdown + "        + {}\n".format(edition)
        return markdown


class CreateHTML(CreatePage):

    def write_results(self, work_dict):
        """

        :param work_dict: the dictionary containing all the authors, works, and editions
        :type work_dict: {urn: {"name": str, "works": {urn: {"editions": [edition1, edition2]}}}}
        :return: the formatted markdown string
        :rtype: str
        """
        html = self.head
        for a in sorted(work_dict.keys(), key=lambda x: work_dict[x]["name"].lower()):
            html = html + "<li>\n{}<strong> - {:,} words</strong>\n\n<ul>".format(work_dict[a]["name"], self.author_words[a])
            for work in sorted(work_dict[a]["works"].keys(), key=lambda x: work_dict[a]["works"][x]["name"].lower()):
                html = html + "<li>\n{}\n".format(work_dict[a]["works"][work]["name"])
                for edition in work_dict[a]["works"][work]["editions"]:
                    html = html + "<ul>\n<li>\n{}\n</li>\n</ul>\n".format(edition)
                html = html + "</li>\n"
            html = html + "</ul>\n</li>\n"
        html += "<p><strong>Word Counts by Source:</strong><br>"
        for k, v in sorted(self.source_words.items(), key=lambda x: x[1], reverse=True):
            html += "<strong>{}:</strong> {:,}<br>".format(k, v)
        html += "</p>"
        html = html + self.foot
        return html

def cmd():
    parser = argparse.ArgumentParser(description='Creates a Github page for a local CTS-compliant Github repository.')
    parser.add_argument('--orig', default='../data', help='The location of the local Github repository.')
    parser.add_argument('--dest', default="./index.html", help='The file in which you want to save your page.')
    parser.add_argument('--out', default="html", help='The format in which you want to save your results.')
    parser.add_argument('--head', default="./header.txt", help='The name of the file that contains the header for your HTML file.')
    parser.add_argument('--foot', default='./footer.txt',help='The name of the file that contains the footer for your HTML file.')
    parser.add_argument('--url_base', help='The string that will serve as the base URL for the links to the text files in the repository.')
    parser.add_argument('--hook_results', default="../results.json", help='The location of the HookTest results JSON file.')
    args = parser.parse_args()
    CreateHTML(**vars(args)).run_all()

if __name__ == '__main__':
    cmd()