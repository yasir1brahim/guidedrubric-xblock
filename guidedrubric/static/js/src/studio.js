function GuidedRubricXBlock(runtime, element) {
    console.log("================ScormStudioXBlock=====================")

    var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

    $(element).find('.save-button').bind('click', function () {
        var form_data = new FormData();
        let assistant_name = $(element).find('input[name=assistant_name]').val();
        let assistant_instructions = $(element).find('input[name=assistant_instructions]').val();
        let assistant_model = $(element).find('input[name=assistant_model]').val();
        let knowledge_base = $(element).find('#knowledge_base').prop('files')[0];
        let completion_message = $(element).find('input[name=completion_message]').val();
        let max_tokens_per_user = $(element).find('input[name=max_tokens_per_user]').val();

        form_data.append('assistant_name', assistant_name);
        form_data.append('assistant_instructions', assistant_instructions);
        form_data.append('assistant_model', assistant_model);
        form_data.append('knowledge_base', knowledge_base);
        form_data.append('completion_message', completion_message);
        form_data.append('max_tokens_per_user', max_tokens_per_user);
        
        console.log("form_data ===>", form_data)
        
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
                            "title": "Scorm component save error"
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
