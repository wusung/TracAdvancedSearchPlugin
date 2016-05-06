
function jump_page(start_point_list, page, size) {
    var url = get_page_url(start_point_list, page);
    document.location.search = "?" + url;
    return false;
}

function get_page_url(start_point_list, page, size) {
	var form = $('#fullsearch');
	var query_string = form.serialize();
	var page = parseInt(page);
	query_string = query_string.replace(new RegExp("page=\\d+"), 'page='+page);
	// Join start points
	//query_string += '&' + $.param(start_point_list);
	query_string += '&PyElasticSearchBackEnd=' + (page * size);

	return query_string;
}

function next_page(start_point_list) {
	var form = $('#fullsearch');

	query_string = form.serialize();
	// Increase page count
	var page = parseInt(form.find('input[name=page]').val()) + 1;
	query_string = query_string.replace(new RegExp("page=\\d+"), 'page='+page);

	// Set start points
	query_string += '&' + $.param(start_point_list)

	document.location.search = '?' + query_string;
	return false;
}

function add_author_input(elem) {
	$(elem).parent('div').before(
		'<div><input type="text" name="author"/> ' +
		'<a href="#" onclick="return remove_author_input(this)">remove</a></div>'
	);
	return false;
}

function remove_author_input(elem) {
	$(elem).parent('div').remove();
	return false;
}

$(document).ready(function() {
	$('#fullsearch input').change(function() {
		$('#fullsearch input[name="page"]').val(1);
	})
    var search = $('link[rel=search]'); 
    $(search).attr('href', $(search).attr('href').replace('search', 'advsearch'));
})
