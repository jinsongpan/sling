# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Workflow builder for downloading wiki dumps"""

import os
import urllib2

from workflow import *
import corpora
import sling.flags as flags
import sling.log as log

# Task for downloading wiki dumps.
class UrlDownload:
  def run(self, task):
    # Get task parameters.
    name = task.param("shortname")
    url = task.param("url")
    chunksize = task.param("chunksize", 64 * 1024)
    output = task.output("output")
    log.info("Download " + name + " from " + url)

    # Make sure directory exists.
    directory = os.path.dirname(output.name)
    if not os.path.exists(directory): os.makedirs(directory)

    # Do not overwrite existing file.
    if os.path.exists(output.name):
      raise Exception("file already exists: " + output.name)

    # Download from url to file.
    conn = urllib2.urlopen(url)
    total_bytes = "bytes_downloaded"
    bytes = name + "_bytes_downloaded"
    with open(output.name, 'wb') as f:
      while True:
        chunk = conn.read(chunksize)
        if not chunk: break
        f.write(chunk)
        task.increment(total_bytes, len(chunk))
        task.increment(bytes, len(chunk))
    log.info(name + " downloaded")

register_task("url-download", UrlDownload)

class DownloadWorkflow:
  def __init__(self, name=None, wf=None):
    if wf == None: wf = Workflow(name)
    self.wf = wf

  #---------------------------------------------------------------------------
  # Wikipedia dumps
  #---------------------------------------------------------------------------

  def wikipedia_dump(self, language=None):
    """Resource for wikipedia dump. This can be downloaded from wikimedia.org
    and contains a full dump of Wikipedia in a particular language. This is
    in XML format with the articles in Wiki markup format."""
    if language == None: language = flags.arg.language
    return self.wf.resource(corpora.wikipedia_dump(language),
                            format="xml/wikipage")

  def download_wikipedia(self, url=None, dump=None, language=None):
    if language == None: language = flags.arg.language
    if url == None: url = corpora.wikipedia_url(language)
    if dump == None: dump = self.wikipedia_dump(language)

    with self.wf.namespace(language + "-wikipedia-download"):
      download = self.wf.task("url-download")
      download.add_params({
        "language": language,
        "url": url,
        "shortname": language + "wiki",
      })
      download.attach_output("output", dump)
      return dump

  #---------------------------------------------------------------------------
  # Wikidata dumps
  #---------------------------------------------------------------------------

  def wikidata_dump(self):
    """Resource for wikidata dump. This can be downloaded from wikimedia.org
    and contains a full dump of Wikidata in JSON format."""
    return self.wf.resource(corpora.wikidata_dump(), format="text/json")

  def download_wikidata(self, url=None, dump=None):
    if url == None: url = corpora.wikidata_url()
    if dump == None: dump = self.wikidata_dump()

    with self.wf.namespace("wikidata-download"):
      download = self.wf.task("url-download")
      download.add_params({
        "url": url,
        "shortname": "wikidata",
      })
      download.attach_output("output", dump)
      return dump
