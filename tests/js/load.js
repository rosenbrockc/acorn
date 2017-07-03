function loadfs() {
//check if browser supports file api and filereader features
if (window.File && window.FileReader && window.FileList && window.Blob) {

   //this is not completely neccesary, just a nice function I found to make the
   //file size format friendlier
   //http://stackoverflow.com/questions/10420352/converting-file-size-in-bytes-to-human-readable
    function humanFileSize(bytes, si) {
        var thresh = si ? 1000 : 1024;
        if(bytes < thresh) return bytes + ' B';
        var units = si ? ['kB','MB','GB','TB','PB','EB','ZB','YB'] :
	    ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
        var u = -1;
        do {
            bytes /= thresh;
            ++u;
        } while(bytes >= thresh);
        return bytes.toFixed(1)+' '+units[u];
    }

    //this function is called when the input loads an image
    function renderDB(file){
        var reader = new FileReader();
        reader.onload = function(event){
	    // console.log("event")
	    // console.log(event)
            source = event.target
	    // console.log("source")
	    // console.log(source)
	    encobj = source.result.split(',')
	    // console.log(encobj)
	    if (encobj[0].includes("base64")) {
		$('#name').html(file.name)
		$('#size').html(humanFileSize(file.size, "MB"))
		$('#type').html(file.type)
		db = JSON.parse(atob(encobj[1]))
		// console.log("Name")
		// console.log(file.name)
		nb = new acorn.Notebook(db, file.name)
		console.log(nb)
		console.log(db)
	    }
        }    
	//when the file is read it triggers the onload event above.
	// console.log("Prefile");
	// console.log(file);
	// console.log("Postfile");
        reader.readAsDataURL(file);
    }
  
    //watch for change on the 
    $('#acorndb').change(function() {
        //grab the first image in the fileList
        //in this example we are only loading one file.
	// console.log("first")
        // console.log(this.files[0].size)
	// console.log(this.files[0])
        renderDB(this.files[0])
    });
    // console.log("Loaded")  
} else {
  alert('The File APIs are not fully supported in this browser.');

}
}
