from distutils.core import setup

from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        [
            'build/cy/ocr_worker.pyx',
            'build/cy/utils/common.pyx',
            'build/cy/utils/container_processor.pyx',
            'build/cy/utils/crnn_recognizer.pyx',
            'build/cy/utils/yolov3_detector.pyx',
        ],
        build_dir='dist/cython_dist',
        compiler_directives={
            'language_level': '3',
        },
        annotate=True,
    ),
)
