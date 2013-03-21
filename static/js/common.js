$(document).ready(function(){
	$('.close-parent').click(function(e) {
		$(this).parent().remove();
	})
});