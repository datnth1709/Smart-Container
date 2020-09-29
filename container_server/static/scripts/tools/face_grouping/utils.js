var faceGroupingUtils = {
    // Generate paging
    generate_paging: function (active_page, num_pages) {
        if (num_pages === 1 || num_pages === null || num_pages === 0) {
            return ''
        }

        const first = 2;
        const last = 2;
        const around = 1;

        let paging = '<li class="page-item active"><a class="page-link" style="color:white !important">' + active_page + '</a></li>';

        if (active_page > 1) {
            let blank = true;
            for (let i = active_page - 1; i > 0; i--) {
                if (active_page - i <= around || i <= first) {
                    paging = '<li class="page-item"><a class="page-link">' + i + '</a></li>' + paging
                } else if (blank) {
                    paging = '<li class="page-item disabled"><a class="page-link">… </a>' + paging;
                    blank = false
                }
            }
        }

        if (active_page < num_pages) {
            let blank = true;
            for (let i = active_page + 1; i <= num_pages; i++) {
                if (i - active_page <= around || i >= num_pages - last) {
                    paging = paging + '<li class="page-item query-image-item"><a class="page-link">' + i + '</a></li>';
                } else if (blank) {
                    paging = paging + '<li class="page-item disabled"><a class="page-link">… </a>';
                    blank = false
                }
            }
        }

        return '<ul class="pagination pagination-sm">' + paging + '</ul>';
    },
    // Copy text to clipboard
    copy_to_clipboard: function (text) {
        let html = '<input id="temp_input" type="text" value="' + text + '">';
        $('body').append(html);
        var copyText = document.getElementById("temp_input");

        copyText.select();
        copyText.setSelectionRange(0, 99999); /*For mobile devices*/

        document.execCommand("copy");

        $('#temp_input').remove()
    },
    // Default values
    defaultSetting: {
        autoGroup: {
            'min_images': 2,
            'matching_probability': 0.6,
        },
        advanceFilter:{
            'paging': true,
            'num_per_page': 60,
            'classify_threshold': 1.0,
            'min_images_in_history': 3,
        }
    }
}
