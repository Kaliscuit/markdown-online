<ul class=entries>
		{% for article in articles %}
		<li>
			<a href="{{ url_for('read', slug=article.slug)}}"/>{{ article.title }}</a>
			<small class="pull-right">{{ article.create_time }}</small>
		</li>
		{% else %}
		<li><em>Nothing here</em>
		{% endfor %}
	</ul>
	
	
	<div class=pagination>
		<ul>
			{% if pagination.has_prev %}
				<li class="prev"><a href="{{ url_for_other_page(pagination.page - 1) }}"></a></li>
			{% else %}
				<li class="prev disabled"><a href="#"></a></li>
			{% endif %}
			{%- for page in pagination.iter_pages() %}
				{% if page %}
					{% if page != pagination.page %}
						<li><a href="{{ url_for_other_page(page) }}">{{ page }}</a></li>
					{% else %}
						<li class="active"><a>{{ page }}</a></li>
				{% endif %}
				{% else %}
					<li class="spaces"><a>...</a></li>
				{% endif %}
			{%- endfor %}
			{% if pagination.has_next %}
				<li class="next"><a href="{{ url_for_other_page(pagination.page + 1) }}"></a></li>
			{% else %}
				<li class="next disabled"><a href="#"></a></li>
			{% endif %}
		</ul>
	</div>