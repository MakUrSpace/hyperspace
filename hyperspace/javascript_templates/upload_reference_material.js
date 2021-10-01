function updateList(){
    var output = document.getElementById('refMatDisplayList')
    var file_names = JSON.parse(document.getElementById('refMatNames').value)
    var children = "";
    file_names.forEach((filename) => {
        children += '<li>' + filename + '</li>'
    })
    if (file_names.length > 1) {
      output.innerHTML = '<ul>'+children+'</ul>';
    } else {
      output.innerHTML = ''
    }
}


function upload_reference_material(){
    var results = []
    var refmat_by_name = {}
    var refmat = document.getElementById('ReferenceMaterial')
    var file_names = JSON.parse(document.getElementById('refMatNames').value)

    $(refmat.files).each(function(i, elem){
        refmat_by_name[elem.name] = elem
    })

    for (var file_index = 0; file_index < refmat.files.length; file_index++){
        file_names.push(refmat.files[file_index].name)
        $.ajax({
            url : `/rest/reference_material/{bounty_id}/${refmat.files[file_index].name}`,
            type : "GET",
            mimeType : "multipart/form-data",
            cache : false,
            contentType : false,
            processData : false
        }).done(function(response){
            response = JSON.parse(response)
            var url = response['url']
            var filename = response['key'].split("/").pop()

            var file_data = new FormData()
            for (var form_key in response){
                if (form_key !== 'url'){
                    file_data.set(form_key, response[form_key])
                }
            }
            file_data.set("ACL", "public-read")
            file_data.set("file", refmat_by_name[filename], filename)

            $.ajax({
                url : url,
                type : "POST",
                data : file_data,
                mimeType : "multipart/form-data",
                cache : false,
                contentType : false,
                processData : false
            }).done(function (_, textStatus, jqXHR) {
                if (jqXHR.status != 204) {
                    file_names.push(`${refmat.files[file_index].name} failed to upload`)
                }
            })
        })
    }
    document.getElementById('refMatNames').value = JSON.stringify(file_names)
    updateList()
}
