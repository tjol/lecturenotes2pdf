import re
from setuptools import setup

def get_long_description():
    with open('README.md', 'r') as readmefile:
        readme_md = readmefile.read()

    first_para = readme_md.split('\n\n')[1]
    no_links = re.sub(r'\[([^\]]+)\]\[[^\]]+\]', r'\1', first_para)

    return no_links.replace('\n', ' ')


setup(
    name="lecturenotes2pdf",
    version="0.1",
    description='Tool to generate PDFs from Acadoid LectureNotes data',
    long_description=get_long_description(),
    author='Thomas Jollans',
    author_email='tjol@tjol.eu',

    url='https://github.com/tjol/lecturenotes2pdf',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',

        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Topic :: Utilities',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        'Natural Language :: English'
    ],


    packages=['lecturenotes2pdf'],
    install_requires=['reportlab>=2.5'], # reportlab 2.5 is in EL7, and works.

    entry_points={
        'console_scripts': [
            'lecturenotes2pdf = lecturenotes2pdf.__main__:main'
        ]
    }
)
