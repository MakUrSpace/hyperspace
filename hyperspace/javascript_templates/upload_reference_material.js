function checkedRefMat(){
    var file_names = JSON.parse(document.getElementById('refMatNames').value)
    var checked_file_names = []
    file_names.forEach((filename) => {
        checkbox = document.getElementById(filename)
        if (checkbox.checked) {
            checked_file_names.push(checkbox.name)
        }
    })
    document.getElementById("checkedRefMatNames").value = JSON.stringify(checked_file_names)

    var changeTracker = document.getElementById('changed')
    if (changeTracker !== null){
        changeTrackerValue = JSON.parse(changeTracker.value)
        changeTrackerValue.push("ReferenceMaterial")
        changeTracker.value = JSON.stringify(changeTrackerValue)
    }
}


function updateList(){
    var output = document.getElementById('refMatDisplayList')
    var file_names = JSON.parse(document.getElementById('refMatNames').value)
    var checked_file_names = JSON.parse(document.getElementById('checkedRefMatNames').value)

    var children = "";
    file_names.forEach((filename) => {
        var checked = ''
        if (checked_file_names.includes(filename)) {
            checked = "checked"
        }
        children += `<input type="checkbox" id=${filename} name=${filename} ${checked} onclick="checkedRefMat()">`
        children += `<label for=${filename}>${filename}</label><br>`
    })
    if (file_names.length > 0) {
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
    var checked_file_names = JSON.parse(document.getElementById('checkedRefMatNames').value)

    $(refmat.files).each(function(i, elem){
        refmat_by_name[elem.name] = elem
    })

    for (var file_index = 0; file_index < refmat.files.length; file_index++){
        file_names.push(refmat.files[file_index].name)
        checked_file_names.push(refmat.files[file_index].name)
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
    document.getElementById('checkedRefMatNames').value = JSON.stringify(checked_file_names)
    updateList()
}

window.addEventListener('load', function() {
    console.log('All assets are loaded')
    document.getElementById('BountyId').value = "{bounty_id}"
    return true
})

$(document).ready(function(){
    updateList()
})
