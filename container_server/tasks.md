- filter cho trang inouthistory:
  + container_code: textbox, search dạng contains
  + start_datetime: datetime picker
  + end_datetime: datetime picker
  + inout: chọn
    + -1: in
    + 1: out
    + 0: unknown
    + -2: all
  + container_length: chọn
    + "": all
    + "-": unknown
    + "2": 20 feet
    + "4": 40 feet
    + "L": 45 feet
    + "M": 48 feet
  + container_height: chọn
    + "": all
    + "-": unknown
    + "0": 8 feet
    + "2": 8 feet 6 inches
    + "5": 9 feet 6 inches
  + ocr_camera: chọn
    + lấy từ danh sách camera có trường user_for_ocr = True
    + thêm lựa chọn "all"
- :heavy_check_mark: Export dạng zip có hyperlink
- chuyển static file trong html template từ dạng cdn sang dạng local
- Auto xóa file export ở server sau khi người dùng download xong
- Data server
- Compile cython
- Chuẩn script, soft deploy ubuntu (offline)
