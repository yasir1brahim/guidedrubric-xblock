/* Javascript for GuidedRubricXBlock. */
function GuidedRubricXBlock(runtime, element) {
    var block_last_phase_id = parseInt($(document).find('#last_phase_id').val());
    var handlerUrl = runtime.handlerUrl(element, 'studio_submit');


    $(element).find('#guided_rubric_add_phase').bind('click', function () {
        block_last_phase_id+=1;
        let phaseName = `<li class="field comp-setting-entry is-set">
        <div class="wrapper-comp-setting">
            <label class="label setting-label" for="phase_name_`+ block_last_phase_id + `">Phase Name</label>
            <input class="input setting-input phase-input" name="phase_name_` + block_last_phase_id +`"id="phase_name_`+ block_last_phase_id +`" value="" type="text" required/>
        </div>
        <div class="wrapper-comp-setting">
            <label class="label setting-label" for="phase_question_`+block_last_phase_id+`">Question</label>
            <input class="input setting-input phase-input" name="phase_question_`+ block_last_phase_id + `" id="phase_question_` +block_last_phase_id +`" value="" type="text" required/>
        </div>
    </li>`;

    $('.list-input.settings-list').append(phaseName)
    });


    $(element).find('.save-button').bind('click', function () {

        var form = document.getElementById('guided_rubric_form');
        var invalidFields = Array.from(form.querySelectorAll(':invalid')).reverse();
        if (invalidFields.length > 0)
        {
            invalidFields.forEach(function(field) {
                field.reportValidity();
            });
            return;
        }


        var form_data = new FormData();
        let assistant_name = $(element).find('input[name=assistant_name]').val();

        let phase_name = $(element).find('#phase_name').val();
        let phase_question = $(element).find('#phase_question').val();
        let last_phase_id = parseInt($(element).find('#last_phase_id').val());
        let phases = [{phase_name:phase_name}];
        let block_phases = JSON.parse($('#json_phases').val());
        //block_phases.push({phase_id: last_phase_id+1,phase_name:phase_name, phase_question:phase_question})
        
        console.log('========phase ids')
        console.log(last_phase_id)
        console.log(block_last_phase_id)
        if (block_last_phase_id > last_phase_id)
        {
            for (var i = last_phase_id +1; i<=block_last_phase_id; i++)
            {
                let phase_name = $(element).find('#phase_name_'+i).val();  
                let phase_question = $(element).find('#phase_question_'+i).val(); 
                block_phases.push({phase_id: i, phase_name:phase_name,phase_question:phase_question})
            }
        }

        form_data.append('assistant_name', assistant_name);
        form_data.append('phases', JSON.stringify(block_phases));
        form_data.append('last_phase_id', block_last_phase_id);
        runtime.notify('save', {
            state: 'start'
        });

        $(this).addClass("disabled");
        $.ajax({
            url: handlerUrl,
            dataType: 'json',
            cache: false,
            contentType: false,
            processData: false,
            data: form_data,
            type: "POST",
            complete: function () {
                $(this).removeClass("disabled");
            },
            success: function (response) {
                if (response.errors.length > 0) {
                    response.errors.forEach(function (error) {
                        runtime.notify("error", {
                            "message": error,
                            "title": "Guided rubric component save error"
                        });
                    });
                } else {
                    runtime.notify('save', {
                        state: 'end'
                    });
                }
            }
        });

    });

    $(element).find('.cancel-button').bind('click', function () {
        runtime.notify('cancel', {});
    });

}
