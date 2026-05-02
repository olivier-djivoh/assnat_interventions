(function($) {
    $(document).ready(function() {
        console.log('jQuery ready');
        
        // Forcer l'exécution après un délai
        setTimeout(init, 500);
        
        function init() {
            var direction = $('#id_direction');
            var service = $('#id_service');
            var division = $('#id_division');
            
            console.log('Direction:', direction.length);
            console.log('Service:', service.length);
            console.log('Division:', division.length);
            
            if (direction.length && service.length && division.length) {
                console.log('Champs trouvés, initialisation...');
                
                direction.change(function() {
                    var dirId = $(this).val();
                    console.log('Direction change:', dirId);
                    
                    service.empty().append('<option value="">---------</option>');
                    division.empty().append('<option value="">---------</option>');
                    
                    if (dirId) {
                        $.getJSON('/comptes/api/services/', {direction: dirId})
                            .done(function(data) {
                                console.log('Services reçus:', data);
                                $.each(data, function(i, item) {
                                    service.append($('<option>', {
                                        value: item.id,
                                        text: item.nom
                                    }));
                                });
                            });
                    }
                });
                
                service.change(function() {
                    var svcId = $(this).val();
                    console.log('Service change:', svcId);
                    
                    division.empty().append('<option value="">---------</option>');
                    
                    if (svcId) {
                        $.getJSON('/comptes/api/divisions/', {service: svcId})
                            .done(function(data) {
                                console.log('Divisions reçues:', data);
                                $.each(data, function(i, item) {
                                    division.append($('<option>', {
                                        value: item.id,
                                        text: item.nom
                                    }));
                                });
                            });
                    }
                });
            }
        }
    });
})(django.jQuery);