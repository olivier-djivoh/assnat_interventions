(function($) {
    $(document).ready(function() {
        function updateServices() {
            var directionId = $('#id_direction').val();
            var serviceSelect = $('#id_service');
            var divisionSelect = $('#id_division');
            
            serviceSelect.empty().append('<option value="">---------</option>');
            divisionSelect.empty().append('<option value="">---------</option>');
            
            if (!directionId) return;
            
            $.ajax({
                url: '/comptes/api/services/',
                data: { direction: directionId },
                dataType: 'json',
                success: function(data) {
                    data.forEach(function(service) {
                        serviceSelect.append(
                            $('<option>', {
                                value: service.id,
                                text: service.nom
                            })
                        );
                    });
                }
            });
        }

        function updateDivisions() {
            var serviceId = $('#id_service').val();
            var divisionSelect = $('#id_division');
            
            divisionSelect.empty().append('<option value="">---------</option>');
            
            if (!serviceId) return;
            
            $.ajax({
                url: '/comptes/api/divisions/',
                data: { service: serviceId },
                dataType: 'json',
                success: function(data) {
                    data.forEach(function(division) {
                        divisionSelect.append(
                            $('<option>', {
                                value: division.id,
                                text: division.nom
                            })
                        );
                    });
                }
            });
        }

        $('#id_direction').change(updateServices);
        $('#id_service').change(updateDivisions);
    });
})(django.jQuery);