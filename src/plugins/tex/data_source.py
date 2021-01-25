import os
import shutil
import tempfile
import subprocess


def tex2pic(equation, output, border=2, resolution=1000):
    packages = r"""
\usepackage{amsmath}
    """

    inline = r"""% latex file generated by tex2pic
\documentclass[border={}pt]{{standalone}}
{}
\begin{{document}}
    $\displaystyle
        {}
    $
\end{{document}}
    """.format(border, packages, equation)

    multi_line = r"""% latex file generated by tex2pic
\documentclass[border={}pt, varwidth=20cm]{{standalone}}
{}
\begin{{document}}
    \begin{{equation*}}
        {}
    \end{{equation*}}
\end{{document}}
    """.format(border, packages, equation)

    fmt = os.path.splitext(output)[-1][1:]

    # create temporary directory and filenames
    tmp_dir = tempfile.mkdtemp()
    tmp_tex = os.path.join(tmp_dir, "tmp.tex")
    tmp_pdf = os.path.join(tmp_dir, "tmp.pdf")
    tmp_out = os.path.join(tmp_dir, "tmp." + fmt)

    # write the tmp tex file
    with open(tmp_tex, 'w') as f:
        if r'\\' in equation:
            f.write(multi_line)
        else:
            f.write(inline)

    # compile the tex file in tmp_dir
    stdout = open(os.devnull, 'w')
    p_open = subprocess.Popen("pdflatex -interaction=nonstopmode -pdf %s" % tmp_tex,
                              shell=True, cwd=tmp_dir, stdout=stdout, stderr=stdout)
    p_open.wait()
    stdout.close()

    # return if not compiled
    if p_open.returncode != 0:
        return False

    # convert in tmp_dir
    formats = {'jpg': 'jpg', 'jpeg': 'jpg', 'png': 'png', 'tiff': 'tiff', 'ppm': ''}
    if fmt in formats.keys():
        convert_cmd = "pdftoppm -r %d -%s %s > %s" % (resolution, formats[fmt], tmp_pdf, tmp_out)
        subprocess.check_call(convert_cmd, shell=True)

    # return the actual output
    if output:
        shutil.copy(tmp_out, output)

    # remove tmp files
    shutil.rmtree(tmp_dir)

    return True
