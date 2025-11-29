function removeConfiguration() {
    while (document.querySelectorAll('div.dynamic-configuration_set').length){
	document.querySelector('div.dynamic-configuration_set .inline-deletelink').click();
    }
}

function addAnotherConfiguration() {
    document.querySelector('#configuration_set-group > fieldset > div.add-row > a').click();
}

function setConfiguration(e) {
    const parentFieldset = document.querySelector('fieldset.module[aria-labelledby="configuration_set-heading"]');
    switch(e.target.value){{% for service in service_list %}
	case "{{ service.pk }}":
	    removeConfiguration();{% for configuration in service.defaultconfiguration_set.all %}
	    addAnotherConfiguration();
	    var itemList = parentFieldset.querySelectorAll('div.inline-related.last-related.dynamic-configuration_set');
	    const item{{ configuration.pk }} = itemList[itemList.length-1];
	    const key{{ configuration.pk }} = document.getElementById(`id_${item{{ configuration.pk }}.id}-key`);
	    const value{{ configuration.pk }} = document.getElementById(`id_${item{{ configuration.pk }}.id}-value`);
	    const valueType{{ configuration.pk }} = document.getElementById(`id_${item{{ configuration.pk }}.id}-value_type`);
	    key{{ configuration.pk }}.value = "{{ configuration.key|escapejs }}";
	    value{{ configuration.pk }}.value = "{{ configuration.value|escapejs }}";
	    valueType{{ configuration.pk }}.value = "{{ configuration.value_type.pk }}";{% endfor %}
	break;{% endfor %}
    }
}

function ready(e) {
    if (!e.target.querySelector('.inline-related.has_original.dynamic-configuration_set')){
	const serviceSelector = e.target.getElementById('id_service');
	serviceSelector.addEventListener('change', setConfiguration);
	console.log('auto-configuration has been loaded');
    }
}
window.addEventListener('load', ready);
