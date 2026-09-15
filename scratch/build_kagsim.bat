@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "c:\Users\Sundareswaran\Kagriculture\external_repos\kaggriculture-cppsim"
python setup.py build_ext --inplace
python setup.py install
