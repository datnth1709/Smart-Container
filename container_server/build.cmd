echo Build cython
xcopy /F /Y ocr_worker\ocr_worker.py build\cy\ocr_worker.pyx
xcopy /F /Y ocr_worker\utils\common.py build\cy\utils\common.pyx
xcopy /F /Y ocr_worker\utils\container_processor.py build\cy\utils\container_processor.pyx
xcopy /F /Y ocr_worker\utils\crnn_recognizer.py build\cy\utils\crnn_recognizer.pyx
xcopy /F /Y ocr_worker\utils\yolov3_detector.py build\cy\utils\yolov3_detector.pyx
python3.6 compile_cython.py build_ext --build-lib dist/cython_dist --compiler=mingw32 -DMS_WIN64
RD /Q /S dist\cython_dist\build
