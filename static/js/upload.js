$(function() {
    $('#fileupload').on('click', function() {
          $('#file').trigger('click');
    });
    $('#file').change(function() {
        event.preventDefault();
        var form_data = new FormData($('#uploadform')[0]);
        $.ajax({
            type: 'POST',
            url: '/upload',
            data: form_data,
            contentType: false,
            processData: false,
            dataType: 'json'
        }).done(function(data, textStatus, jqXHR){
            console.log(data);
            console.log(textStatus);
            console.log(jqXHR);
            console.log('Success!');
            $("#resultFilename").text(data['name']);
            $("#resultFilesize").text(data['size']);
        }).fail(function(data){
            alert('error!');
        });
    });
    $('#previewButton').click(function() {
        event.preventDefault();
        var json = JSON.stringify($('#text').val());
        $.ajax({
            type: 'POST',
            url: '/preview',
            data: json,
            contentType: 'application/json',
            dataType: 'json',
        }).done(function(data){
            console.log('Success!');
            console.log(data.preview);
            $("#preview").html(data.preview);
        });
    });
});
