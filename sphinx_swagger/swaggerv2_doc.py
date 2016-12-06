# -*- coding: utf-8 -*-
from docutils import nodes
import traceback

from docutils.parsers.rst import Directive

from sphinx.locale import _

import requests
import json

class swaggerv2doc(nodes.Admonition, nodes.Element):
    pass

def visit_swaggerv2doc_node(self, node):
    self.visit_admonition(node)

def depart_swaggerv2doc_node(self, node):
    self.depart_admonition(node)

class SwaggerV2DocDirective(Directive):

    # this enables content in the directive
    has_content = True

    def processSwaggerURL(self, url):
        r = requests.get(url)
        return r.json()

    def create_item(self, key, value):
        para = nodes.paragraph()
        para += nodes.strong('', key)
        para += nodes.Text(value)

        item = nodes.list_item()
        item += para

        return item

    def expand_values(self, list):
        expanded_values = ''
        for value in list:
            expanded_values += value + ' '

        return expanded_values

    def cell(self, contents):
        if isinstance(contents, basestring):
            contents = nodes.paragraph(text=contents)
        return nodes.entry('', contents)

    def row(self, cells):
        return nodes.row('', *[self.cell(c) for c in cells])

    def create_table(self, head, body, colspec=None):
        table = nodes.table()
        tgroup = nodes.tgroup()
        table.append(tgroup)

        # Create a colspec for each column
        if colspec is None:
            colspec = [1 for n in range(len(head))]

        for width in colspec:
            tgroup.append(nodes.colspec(colwidth=width))

        # Create the table headers
        thead = nodes.thead()
        thead.append(self.row(head))
        tgroup.append(thead)

        # Create the table body
        tbody = nodes.tbody()
        tbody.extend([self.row(r) for r in body])
        tgroup.append(tbody)

        return table

    def make_parameters(self, parameters):
        entries = []

        head = ['Name', 'Position', 'Description', 'Type']
        body = []
        for param in parameters:
            row = []
            row.append(param.get('name', ''))
            row.append(param.get('in', ''))
            row.append(param.get('description', ''))
            row.append(param.get('type', ''))

            body.append(row)

        table = self.create_table(head, body)

        paragraph = nodes.paragraph()
        paragraph += nodes.strong('', 'Parameters')

        entries.append(paragraph)
        entries.append(table)

        return entries

    def make_method(self, path, method_type, method):
        swagger_node = swaggerv2doc(path)
        swagger_node += nodes.title(path, method_type.upper() + ' ' + path)

        paragraph = nodes.paragraph()
        paragraph += nodes.Text(method['summary'])

        bullet_list = nodes.bullet_list()
        bullet_list += self.create_item('Description: ', method.get('description', ''))
        bullet_list += self.create_item('Consumes: ', self.expand_values(method.get('consumes', '')))
        bullet_list += self.create_item('Produces: ', self.expand_values(method.get('produces', '')))
        paragraph += bullet_list

        swagger_node += paragraph

        swagger_node += self.make_parameters(method['parameters'])

        return [swagger_node]

    def group_tags(self, api_desc):
        groups = {}

        
        for path, methods in api_desc['paths'].items():
            for method_type, method in methods.items():
                for tag in method['tags']:
                    if tag not in groups:
                        groups[tag]=[]
                    groups[tag].append((path, method_type, method))

        return groups

    def create_section(self, title):
        section = nodes.section(ids=[title])
        section += nodes.title(title, title)
        return section

    def run(self):
        api_url = self.content[0]

        if len(self.content) > 1:
            selected_tags = self.content[1:]
        else:
            selected_tags = []

        try:
            api_desc = self.processSwaggerURL(api_url)

            groups = self.group_tags(api_desc)

            entries = []
            for tag_name, methods in groups.items():
                if tag_name in selected_tags or len(selected_tags) == 0:
                    section = self.create_section(tag_name)

                    for path, method_type, method in methods:
                        section += self.make_method(path, method_type, method)

                    entries.append(section)

            return entries
        except Exception as e:
            error_message = 'Unable to process URL: %s' % api_url
            print(error_message)
            traceback.print_exc()

            error = nodes.error('')
            para_error = nodes.paragraph()
            para_error += nodes.Text(error_message + '. Please check that the URL is a valid Swagger api-docs URL and it is accesible')
            para_error_detailed = nodes.paragraph()
            para_error_detailed = nodes.strong('Processing error. See console output for a more detailed error')
            error += para_error
            error += para_error_detailed
            return [error]
