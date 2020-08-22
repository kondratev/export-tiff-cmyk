# -*- coding: utf-8 -*-
#!/usr/bin/env python

#  Copyright (C) 2010, 2011 Jonatã Bolzan <jonata@jonata.org>
#  Copyright (C) 2011  Anton Katsarov <anton@katsarov.org>
#
#  This file is part of Export-Tiff-CMYK.
#
#  Export-Tiff-CMYK is free software: you
#  can redistribute it and/or modify it under the terms of the GNU
#  General Public License (GNU GPL) as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option)
#  any later version.  The code is distributed WITHOUT ANY WARRANTY
#  without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.
#
#  As additional permission under GNU GPL version 3 section 7, you
#  may distribute non-source (e.g., minimized or compacted) forms of
#  that code without the copy of the GNU GPL normally required by
#  section 4, provided you include this license notice and a URL
#  through which recipients can access the Corresponding Source.
#
#  END OF LICENSE HEADER

# These two lines are only needed if you don't put the script directly into
# the installation directory
import subprocess
import re
import os
import tempfile
import simplestyle
import inkex
import sys
sys.path.append('/usr/share/inkscape/extensions')


class ExportTIFF(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("-p", "--icc_profile", action="store",
                                     type=inkex.Boolean, dest="icc_profile", default=True, help="ICC Profile")
        self.arg_parser.add_argument("-r", "--resolution", action="store", type=int,
                                     dest="resolution", default=300, help="Resolution for rasterization (dpi)")
        self.arg_parser.add_argument("-k", "--set_overprint_black", action="store",
                                     type=inkex.Boolean, dest="set_overprint_black", default=True, help="Preserve black")
        self.arg_parser.add_argument("-a", "--set_alpha", action="store", type=inkex.Boolean,
                                     dest="set_alpha", default=True, help="Preserve transparency")

    def output(self):
        out = open(tempfile.gettempdir() + os.sep + 'final.tif', 'rb')
        if os.name == 'nt':
            try:
                import msvcrt
                msvcrt.setmode(1, os.O_BINARY)
            except:
                pass
        sys.stdout.buffer.write(out.read())
        out.close()

    def effect(self):
        if os.sep == "\\":
            ff = open(os.getenv("APPDATA") + '\inkscape\preferences.xml', 'r')
            inkscape_config = ff.read()
            ff.close()
        else:
            ff = open(os.getenv("HOME") + '/.config/inkscape/preferences.xml', 'r')
            inkscape_config = ff.read()
            ff.close()

        ff = open(self.options.input_file, 'r')
        svg = ff.read()
        ff.close()

        def padronizar_cores_svg():
            def trocar_cores(origin, tipo_cor):
                for i in range(len(str(origin).split(tipo_cor + ':'))):
                    if str(str(origin).split(tipo_cor + ':')[i].split(';')[0]) in simplestyle.svgcolors.keys():
                        numeros_da_cor = simplestyle.formatColoria(simplestyle.parseColor(
                            str(str(origin).split(tipo_cor + ':')[i].split(';')[0])))
                        origin = str(origin).replace(
                            ':' + str(str(origin).split(tipo_cor + ':')[i].split(';')[0]) + ';', ':' + numeros_da_cor + ';')
                return origin

            colortypes = ['fill', 'stop-color', 'flood-color', 'lighting-color', 'stroke']
            for i in range(len(colortypes)):
                svg_padronizado = trocar_cores(svg, colortypes[i])

            return svg_padronizado

        def o_que_exportar():
            return ["--export-area-page"]
            '''if self.options.export_area != "":
                export_area = self.options.export_area.split(",")
            else:
                export_area = []
                for node in self.document.xpath('//svg:g', namespaces=inkex.NSS):
                    for child in node:
                        if "cmyk" in child.get('id'):
                            export_area.append("--export-id=" + child.get('id'))
            return export_area'''

        def calculateCMYK(red, green, blue):
            C = float()
            M = float()
            Y = float()
            K = float()

            if 1.00 - red < 1.00 - green:
                K = 1.00 - red
            else:
                K = 1.00 - green

            if 1.00 - blue < K:
                K = 1.00 - blue

            if K != 1.00:
                C = (1.00 - red - K) / (1.00 - K)
                M = (1.00 - green - K) / (1.00 - K)
                Y = (1.00 - blue - K) / (1.00 - K)

            return [C, M, Y, K]

        def converter_elementos_para_imagens():
            areas_a_exportar = o_que_exportar()

            arquivo_svg_C = padronizar_cores_svg()
            arquivo_svg_M = padronizar_cores_svg()
            arquivo_svg_Y = padronizar_cores_svg()
            arquivo_svg_K = padronizar_cores_svg()

            def removeK(origem):
                def zerar_opacidade(valor):
                    return str(valor.group()).split('opacity:')[0] + "opacity:0;"
                return re.sub("#000000;fill-opacity:[0-9.]+;", zerar_opacidade, re.sub("#000000;stop-opacity:[0-9.]+;", zerar_opacidade, re.sub("#000000;stroke-opacity:[0-9.]+;", zerar_opacidade, re.sub("#000000;flood-opacity:[0-9.]+;", zerar_opacidade, re.sub("#000000;lighting-opacity:[0-9.]+;", zerar_opacidade, origem)))))

            def representC(value):
                # returns CMS color if available
                if (re.search("icc-color", value.group())):
                    #return simplestyle.formatColor3f(float(1.00 - float(re.split('[,\)\s]+', value.group())[2])), float(1.00), float(1.00))
                    return str(inkex.Color((float(1.00 - float(re.split('[,\)\s]+', value.group())[2])), float(1.00), float(1.00))))
                else:
                    #red = float(simplestyle.parseColor(str(value.group()))[0]/255.00)
                    #green =float(simplestyle.parseColor(str(value.group()))[1]/255.00)
                    #blue = float(simplestyle.parseColor(str(value.group()))[2]/255.00)
                    #return simplestyle.formatColor3f(float(1.00 - calculateCMYK(red, green, blue)[0]), float(1.00), float(1.00))
                    red = float(inkex.Color(str(value.group()))[0]/255.00)
                    green =float(inkex.Color(str(value.group()))[1]/255.00)
                    blue = float(inkex.Color(str(value.group()))[2]/255.00)
                    return str(inkex.Color((float(1.00 - calculateCMYK(red, green, blue)[0]), float(1.00), float(1.00))))

            def representM(value):
                # returns CMS color if available
                if (re.search("icc-color", value.group())):
                    #return simplestyle.formatColor3f(float(1.00 - float(re.split('[,\)\s]+', value.group())[2])), float(1.00), float(1.00))
                    return str(inkex.Color((float(1.00 - float(re.split('[,\)\s]+', value.group())[2])),float(1.00), float(1.00))))
                else:
                    #red = float(simplestyle.parseColor(str(value.group()))[0]/255.00)
                    #green = float(simplestyle.parseColor(str(value.group()))[1]/255.00)
                    #blue = float(simplestyle.parseColor(str(value.group()))[2]/255.00)
                    #return simplestyle.formatColor3f(float(1.00), float(1.00 - calculateCMYK(red, green, blue)[1]), float(1.00))
                    red = float(inkex.Color(str(value.group()))[0]/255.00)
                    green =float(inkex.Color(str(value.group()))[1]/255.00)
                    blue = float(inkex.Color(str(value.group()))[2]/255.00)
                    return str(inkex.Color((float(1.00), float(1.00 - calculateCMYK(red, green, blue)[1]), float(1.00))))

            def representY(value):
                # returns CMS color if available
                if (re.search("icc-color", value.group())):
                    #return simplestyle.formatColor3f(float(1.00), float(1.00), float(1.00 - float(re.split('[,\)\s]+', value.group())[4])))
                    return str(inkex.Color((float(1.00), float(1.00), float(1.00 - float(re.split('[,\)\s]+', value.group())[4])))))
                else:
                    #red = float(simplestyle.parseColor(str(value.group()))[0]/255.00)
                    #green = float(simplestyle.parseColor(str(value.group()))[1]/255.00)
                    #blue = float(simplestyle.parseColor(str(value.group()))[2]/255.00)
                    #return simplestyle.formatColor3f(float(1.00), float(1.00), float(1.00 - calculateCMYK(red, green, blue)[2]))
                    red = float(inkex.Color(str(value.group()))[0]/255.00)
                    green =float(inkex.Color(str(value.group()))[1]/255.00)
                    blue = float(inkex.Color(str(value.group()))[2]/255.00)
                    return str(inkex.Color((float(1.00), float(1.00), float(1.00 - calculateCMYK(red, green, blue)[2]))))

            def representK(value):
                # returns CMS color if available
                if (re.search("icc-color", value.group())):
                    #return simplestyle.formatColor3f(float(1.00 - float(re.split('[,\)\s]+', value.group())[5])), float(1.00 - float(re.split('[,\)\s]+', value.group())[5])), float(1.00 - float(re.split('[,\)\s]+', value.group())[5])))
                    return str(inkex.Color((float(1.00 - float(re.split('[,\)\s]+', value.group())[5])), float(1.00 - float(re.split('[,\)\s]+', value.group())[5])), float(1.00 - float(re.split('[,\)\s]+', value.group())[5])))))
                else:
                    #red = float(simplestyle.parseColor(str(value.group()))[0]/255.00)
                    #green = float(simplestyle.parseColor(str(value.group()))[1]/255.00)
                    #blue = float(simplestyle.parseColor(str(value.group()))[2]/255.00)
                    #return simplestyle.formatColor3f(float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]))
                    red = float(inkex.Color(str(value.group()))[0]/255.00)
                    green =float(inkex.Color(str(value.group()))[1]/255.00)
                    blue = float(inkex.Color(str(value.group()))[2]/255.00)
                    return str(inkex.Color((float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]), float(1.00 - calculateCMYK(red, green, blue)[3]))))

            if (self.options.set_overprint_black):
                # RegEx Matches CMS colors too
                ff = open(tempfile.gettempdir() + os.sep + "separationC.svg", "w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representC, removeK(arquivo_svg_C)))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationM.svg", "w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representM, removeK(arquivo_svg_M)))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationY.svg", "w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representY, removeK(arquivo_svg_Y)))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationK.svg", "w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representK, arquivo_svg_K))
                ff.close()
            else:
                ff = open(tempfile.gettempdir() + os.sep + "separationC.svg","w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representC, arquivo_svg_C))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationM.svg","w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representM, arquivo_svg_M))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationY.svg","w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representY, arquivo_svg_Y))
                ff.close()
                ff = open(tempfile.gettempdir() + os.sep + "separationK.svg","w")
                ff.write(re.sub("#[a-fA-F0-9]{6}( icc-color\(.*?\))?", representK, arquivo_svg_K))
                ff.close()

            resolution = str(int(self.options.resolution))

            # if self.options.specialeffects_exclusively:
            #areas_a_exportar_only = '--export-id-only'
            # else:
            areas_a_exportar_only = ''

            if (self.options.set_alpha):
                alpha = ""
            else:
                alpha = " export-background:white; "
            color_space = "CMYK"

            def gerar_pngs():
                string_inkscape_exec = ''
                for i in range(len(areas_a_exportar)):
                    string_inkscape_exec = string_inkscape_exec + "file-open:" + tempfile.gettempdir() + os.sep + "separationC.svg" + "; " + areas_a_exportar[i].replace("--export-area-page", "export-area-page;") + " " + areas_a_exportar_only + " " + alpha + " " + 'export-filename:' + tempfile.gettempdir(
                    ) + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png;" + ' export-dpi:' + resolution + "; export-do;\n"
                    string_inkscape_exec = string_inkscape_exec + "file-open:" + tempfile.gettempdir() + os.sep + "separationM.svg" + "; " + areas_a_exportar[i].replace("--export-area-page", "export-area-page;") + " " + areas_a_exportar_only + " " + alpha + " " + 'export-filename:' + tempfile.gettempdir(
                    ) + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "M.png;" + ' export-dpi:' + resolution + "; export-do;\n"
                    string_inkscape_exec = string_inkscape_exec + "file-open:" + tempfile.gettempdir() + os.sep + "separationY.svg" + "; " + areas_a_exportar[i].replace("--export-area-page", "export-area-page;") + " " + areas_a_exportar_only + " " + alpha + " " + 'export-filename:' + tempfile.gettempdir(
                    ) + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "Y.png;" + ' export-dpi:' + resolution + "; export-do;\n"
                    string_inkscape_exec = string_inkscape_exec + "file-open:" + tempfile.gettempdir() + os.sep + "separationK.svg" + "; " + areas_a_exportar[i].replace("--export-area-page", "export-area-page;") + " " + areas_a_exportar_only + " " + alpha + " " + 'export-filename:' + tempfile.gettempdir(
                    ) + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png;" + ' export-dpi:' + resolution + "; export-do;\n"
                return str.encode(string_inkscape_exec)
            devnull=open(os.devnull, 'w')
#            devnull=open('/tmp/errorlog.txt.ink', 'w')
            devnull.write(str(gerar_pngs()))
            devnull.write(str(areas_a_exportar))
            inkscape_exec = subprocess.Popen(['inkscape --shell'], shell=True, stdout=devnull,
                stderr=devnull, stdin=subprocess.PIPE)  # + ['>', os.devnull])
            inkscape_exec.communicate(input=gerar_pngs())

            for i in range(len(areas_a_exportar)):
                if (self.options.set_alpha):
#                    devnull.write(str(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png",
#                                      '-alpha', 'extract',  tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "mask.png"]))
                    subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png",
                                      '-alpha', 'extract',  tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "mask.png"]).wait()
                    pass
#                devnull.write(str(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png", '-colorspace',
#                                  'CMYK', '-channel', 'C', '-separate', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png"]))
                subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png", '-colorspace',
                                  'CMYK', '-channel', 'C', '-separate', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png"]).wait()
                subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "M.png", '-colorspace',
                                  'CMYK', '-channel', 'M', '-separate', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "M.png"]).wait()
                subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "Y.png", '-colorspace',
                                  'CMYK', '-channel', 'Y', '-separate', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "Y.png"]).wait()
                subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png", '-colorspace',
                                  'CMYK', '-channel', 'K', '-separate', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png"]).wait()
#                devnull.write(str(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "M.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace(
#                    "--export-id=", "").replace("--export-area-page", "final") + "Y.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png", '-set', 'colorspace', 'CMYK', '-combine', tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]))
                subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "C.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "M.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace(
                    "--export-id=", "").replace("--export-area-page", "final") + "Y.png", tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "K.png", '-set', 'colorspace', 'CMYK', '-combine', tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]).wait()
                if (self.options.set_alpha):
#                    devnull.write(str(['composite', '-compose', 'CopyOpacity', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "mask.png", tempfile.gettempdir() + os.sep +
#                                      areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif", tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]))
                    subprocess.Popen(['composite', '-compose', 'CopyOpacity', tempfile.gettempdir() + os.sep + "separated" + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + "mask.png", tempfile.gettempdir() + os.sep +
                                      areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif", tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]).wait()
                    pass
                if (self.options.icc_profile):
                    cmyk_profile = '"' + \
                        inkscape_config.split('id="softproof"')[1].split(
                            'uri="')[1].split('" />')[0] + '"'
                    devnull.write(str(['convert', tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif",
                                      '-profile', cmyk_profile, tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]))
                    devnull.write(str(cmyk_profile))
                    subprocess.Popen(['convert', tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif",
                                      '-profile', cmyk_profile, tempfile.gettempdir() + os.sep + areas_a_exportar[i].replace("--export-id=", "").replace("--export-area-page", "final") + ".tif"]).wait()

            devnull.close()
        converter_elementos_para_imagens()


if __name__ == '__main__':
    effect = ExportTIFF()
    #effect.affect()
    effect.run()
