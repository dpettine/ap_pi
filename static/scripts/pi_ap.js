$(function(){

     $('#wifi-passphrase-Button').click(function(){

            ssid = $("input[name='networks']:checked").val();
            the_attribute = $("input[name='networks']:checked").attr('id')
            the_enc = $("#WiFi-Encryption-"+the_attribute).text().trim();
            the_status = $("#SSID-"+the_attribute).text().trim();

            if (the_status == "Connected"){
                $('#WiFi-Modal-Error').remove();
                $('#staticBackdrop-body').append('<p Id="WiFi-Modal-Error" style="font-size:90%;" class="text-info">The network chosen is already connected!</p>');
            }

            else if ((the_enc != "None") && ( $("#WiFi-password").val() == ""  )){
                $('#WiFi-Modal-Error').remove();
                $('#staticBackdrop-body').append('<p Id="WiFi-Modal-Error" style="font-size:90%;" class="text-warning">Please set a valid WiFi Password/Passphrase</p>');
            }

            else{
                $('#WiFi-Modal-Error').remove();
                $('#wifi-Button-spin').show();
                $('#wifi-passphrase-Button').addClass('disabled');
			    $('#wifi-passphrase-Button').text('Loading..')
			    $('#WiFi-password').prop("disabled", true);
			    $('#WiFi-password-unmask').prop("disabled", true);
			    $('#wifi-modal-close').prop("disabled", true);

                $.ajax({
			    url: '/wifi/wifi-connect',
			    data: { passphrase: "" + $('#WiFi-password').val() + "",
			     ssid: "" + ssid + ""},
			    type: 'POST',
			    success: function(response){
			        $('#wifi-Button-spin').hide();
			        $('#wifi-passphrase-Button').removeClass('disabled');
			        $('#wifi-passphrase-Button').text('Connect')
			        $('#WiFi-password').prop("disabled", false);
			        $('#WiFi-password-unmask').prop("disabled", false);
			        $('#wifi-modal-close').prop("disabled", false);
			        //$('#staticBackdrop').modal('toggle');
			        $("#WiFi-password").hide();
                    $("#WiFi-pwd-umask-div").hide();
                    $("#WiFi-label").hide();

			        if (response['connected'] == true){
                        new_ssid = response['ssid'];
                        $(":radio[value="+new_ssid+"]").attr('checked', 'checked');
                        the_attribute = $(":radio[value="+new_ssid+"]").attr('id');
                        $("#SSID-"+the_attribute).text('Connected')
                        $('#staticBackdrop-body').append('<div id="wifi-connect-result" class="text-info" style="font-size:90%;"> Connected to the network '+new_ssid+'</div>');
			        }

			        else{
			            $('#staticBackdrop-body').append('<div id="wifi-connect-result" class="text-warning" style="font-size:90%;">'+response['error']+'</div>');
			        }

			        console.log("Success", response);
			    },
			    error: function(error){
			        $('#wifi-Button-spin').hide();
			        $('#wifi-passphrase-Button').removeClass('disabled');
			        $('#wifi-passphrase-Button').text('Connect')
			        $('#WiFi-password').prop("disabled", false);
			        $('#WiFi-password-unmask').prop("disabled", false);
			        $('#wifi-modal-close').prop("disabled", false);
			        $("#WiFi-password").hide();
                    $("#WiFi-pwd-umask-div").hide();
                    $("#WiFi-label").hide();

                    $('#staticBackdrop-body').append('<div id="wifi-connect-result" class="text-error" style="font-size:90%;">Error in connecting the network. Please retry !</div>');

			        console.log(error);
			        }
			    });
            }

        });

        $("#WiFi-password-unmask").click(function(){

            if ($("#WiFi-password-unmask").is(":checked")){
                $('#WiFi-password').prop('type','text');
            }

            else{
                $('#WiFi-password').prop('type','password');
            }
          });


        $("#staticBackdrop").on('shown.bs.modal', function (e) {
            // Handler for .load() called.
            the_ssid = $("input[name='networks']:checked").val();
            the_attribute = $("input[name='networks']:checked").attr('id')
            the_enc = $("#WiFi-Encryption-"+the_attribute).text().trim();
            $('#wifi-Button-spin').hide();
			$('#wifi-passphrase-Button').removeClass('disabled');
			$('#WiFi-Modal-Error').remove();
			$("#WiFi-password").val('');
			$('#WiFi-password').prop("disabled", false);
			$('#WiFi-password-unmask').prop("disabled", false);
			$('#wifi-modal-close').prop("disabled", false);
			$("#wifi-connect-result").hide();

            if (the_enc == "None"){
                $("#WiFi-label").text("You are connecting to an unsecured WiFi network. Please consider setting wireless security on your access point !")
                $("#WiFi-password").hide();
                $("#WiFi-pwd-umask-div").hide();

            }
            else{
                $("#WiFi-label").text("Please provide the WiFi Password/Passphrase")
                $("#WiFi-password").show();
                $("#WiFi-pwd-umask-div").show();
            }

            });

});





