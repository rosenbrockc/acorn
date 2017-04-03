//Ipython js injection to handle the Markdown cell rendering so that we can log
//it to the acorn database with a timestamp.
if (typeof window.acorn_ipython == 'undefined' && IPython.notebook.kernel != null) {
    function acorn_log_error(msg) {
	// if (msg.msg_type == "error") {
	//     console.log(msg)
	// };
	console.log(msg);
    };
    var acorn_callbacks = {
	"iopub": { "output": acorn_log_error }
    };
    function acorn_md_handler(event, data) {
	var contents = data.cell.get_text();
	if (contents != "") {
            var _cvar = "_acorn_mdcell = r'''" + contents + "'''\n";
	    var _cid = "_mdcell_id = '" + data.cell.cell_id + "'\n";
            var _cmd = "acorn.ipython.record_markdown(_acorn_mdcell, _mdcell_id)\n";
	    var _evar = "del _acorn_mdcell\ndel _mdcell_id";
            var kcmd = _cvar + _cid + _cmd + _evar;
            IPython.notebook.kernel.execute(kcmd, acorn_callbacks);
	}
    };
    IPython.notebook.events.bind("rendered.MarkdownCell", acorn_md_handler);
    console.log("Bound acorn event handler for 'rendered.MarkdownCell' event.")
    window.acorn_ipython = true;
}
