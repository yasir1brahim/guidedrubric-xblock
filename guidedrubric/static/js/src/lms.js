/* Javascript for GuidedRubricXBlock. */
function GuidedRubricXBlock(runtime, element) {

    let chatMsg = document.getElementById('chat-msg');
    let chatLogs = document.getElementById('chat-logs');
    let sendBtn = document.getElementById('send-btn');
    let skipBtn = document.getElementById('skip-btn');
    let errorMsg = document.getElementById('error-msg');

    // loader
    let loadingMsg = document.createElement('div');
    var overlay = document.createElement("div");
    var loader = document.createElement("div");
    overlay.setAttribute("class", "overlay");
    overlay.setAttribute("id", "overlay-loader");
    loader.setAttribute("class", "lds-dual-ring");
    overlay.appendChild(loader);
    // loadingMsg.classList.add("loading");
    // loadingMsg.appendChild(loader);

    // Handlers
    var handlerUrl = runtime.handlerUrl(element, 'send_message');

    function send_message(message) {
        const completion_token = parseInt(document.getElementById('completion_token').value);
        const max_tokens_per_user = parseInt(document.getElementById('max_tokens_per_user').value);
        const is_staff = document.getElementById('is_staff').value === 'True';

        if(completion_token > max_tokens_per_user && !is_staff){
            alert("You have exceeded the allowed number of tokens. Please contact the course staff")
        }
        else{

        if (message != "skip")
        {
            $('#chat_input_loader').css('display', '')
        }
        return $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify({"message": message}),
            contentType:"application/json; charset=utf-8",
            dataType: "json",
        }).done(function(response) {
            $('#chat_input_loader').css('display', 'none')
            if (response.result === 'success') {
                if (response.response[1]){
                    //var statusElements = document.getElementsByClassName('status');
                    //statusElements[statusElements.length - 1].textContent = "Status: " + response.response[1];
                }
                chatLogs.removeChild(loadingMsg);
                console.log('========calling keep_user_response')
                console.log(message)
                let completion_token = response.response_metadata.completion_token
                $('#completion_token').val(completion_token) 
                keep_user_response(message)
                type_message(response.response);
            } else {
                alert("You've reached the end of the exercise. Hope you learned something!");
                chatLogs.removeChild(loadingMsg);
                document.querySelector('.chat-input').style.display = 'block';
            }
        }).fail(function(error) {
            console.log("An error occurred: ", error);
        });
    }};
    sendBtn.addEventListener('click', function() {
        //let status = document.createElement('div');
        if (!chatMsg.value.trim()) {
            // errorMsg.textContent = "You should enter prompt";
            // return;
            alert("You should enter prompt")
            return;
        }
        document.querySelector('.chat-input').style.display = 'none';
        errorMsg.textContent = "";
        var chat_message = chatMsg.value;
        let newMsg = document.createElement('div');
        //newMsg.textContent = "Your Answer: " + chatMsg.value;
        newMsg.classList.add("my-msg");
        //status.classList.add("status");
        //status.textContent = "Status: Pending";
        chatLogs.appendChild(newMsg);
        //chatLogs.appendChild(status)
        chatLogs.appendChild(loadingMsg);

        last_attempted_phase_id = $('#last_attempted_phase_id').val()

        //chatMsg.value = "";
        $('.micro-ai-btn-container').css('display', 'none')
        send_message(chat_message);
    });
    skipBtn.addEventListener('click', function() {
        var status = document.createElement('div');
        document.querySelector('.chat-input').style.display = 'none';
        errorMsg.textContent = "";
        let newMsg = document.createElement('div');
        //newMsg.textContent = "Your Answer: " + chatMsg.value;
        //status.textContent = "Status: Skip";
        newMsg.classList.add("my-msg");
        //chatLogs.appendChild(newMsg);
        //chatLogs.appendChild(status)
        chatLogs.appendChild(loadingMsg);
        chatMsg.value = "";
        send_message("skip");
    });

    function keep_user_response(user_input)
    {
        console.log('=======keep_user_response')
        console.log(user_input)
        // let phase_id = 1
        // let user_response_div = `<div class="chat-input" style="display: block;">
        //           <textarea id="chat_msg_phase_`+phase_id+`" placeholder="Enter Prompt ... " rows="24" cols="230">`+user_input+`</textarea>
        //         </div>`
        // $('#chat-logs').append(user_response_div)
    }

    // Student reports
    var reportElement = $(element).find(".scorm-reports .report");
    function initReports() {
        if (reportElement.length === 0){
            return;
        }
        $(element).find("button.clear-data").on("click", function () {
            viewReports();
        });
        $(element).find("button.clear-data").on("click", function () {
            reloadReport();
        });

        $.ui.autocomplete(
            {
                source: searchStudents,
                select: setStudentId,
            }, $(element).find(".scorm-reports input.search-students")
        );
    }
    function searchStudents(request, response) {
        var url = runtime.handlerUrl(element, 'scorm_search_students');
        console.log("url ===>", url);
        $.ajax({
            url: url,
            data: {
                'id': request.term
            },
        }).success(function (data) {
            console.log("data",data);
            if (data.length === 0) {
                noStudentFound()
            }
            else if(data.length > 0){
                StudentFound()
            }
            response(data);
        }).fail(function () {
            noStudentFound()
            response([])
        });
    }
    function noStudentFound() {
        reportElement.html("no student found");
        $(element).find(".reload-report").addClass("reports-togglable-off");
    }
    function StudentFound() {
        reportElement.html("Student found");
        $(element).find(".reload-report").addClass("reports-togglable-off");
    }
    function viewReports() {
        // Display reports on button click
        $(element).find(".reports-togglable").toggleClass("reports-togglable-off");
    }
    var studentId = null;
    function viewReport(event, ui) {
        studentId = ui.item.data.student_id;
        getReport(studentId);
    }

    function setStudentId(event, ui){
        studentId = ui.item.data.student_id;
    }
    function reloadReport() {
        getReport(studentId)
    }
    function getReport(studentId) {
        var getReportUrl = runtime.handlerUrl(element, 'scorm_get_student_state');
        $.ajax({
            url: getReportUrl,
            data: {
                'id': studentId
            },
        }).success(function (response) {
            console.log(response);
            let completion_token = response.response_metadata.completion_token
            $('#completion_token').val(completion_token)     
            console.log("SUCCESS");
        }).fail(function () {
            console.log("FAIL");
        }).complete(function () {
            $(element).find(".reload-report").removeClass("reports-togglable-off");
        });
        reportElement.html("Cleared user data");
        
    }




    function type_message(data) {
        debugger;
        console.log('==========removing ai-msg')
        console.log($('.recent-ai-msg'))
        // $('.previous-ai-msg').remove();
        // $('.recent-ai-msg').textContent = ""
        $('.recent-ai-msg').empty()


        chunks = data[4]
        let aiMsg = $('.recent-ai-msg')
        // let aiMsg = document.createElement('div');
        // let question = document.createElement('p');
        // question.classList.add("questions");
        // aiMsg.classList.add("ai-msg");
        // chatLogs.appendChild(aiMsg);
    
        // This function will be called recursively with a delay to simulate streaming
        function displayNextChunk(index) {
            if (index < chunks.length) {
                // Append the current chunk to the aiMsg element
                let current_text = aiMsg.text()
                let new_text = current_text +  chunks[index];
                //aiMsg.textContent += chunks[index];
                $('.chat-input').css('display', 'none');
                aiMsg.text(new_text)
                
                // Call this function again for the next chunk after a short delay
                setTimeout(() => displayNextChunk(index + 1), 100); // Adjust delay as needed
            } else {
                // Once all chunks are displayed, make the input field visible again
                if (data[1] == 'Success' || data[1]==null || data[1]== 'Fail')
                {
                    if (data[2]){
                        question.textContent = data[2];
                        chatLogs.appendChild(question);
                        $('#send-btn').text(data[3])
                    }
                    if (data[2] === null) {
                        allQuestions = document.querySelectorAll('.my-msg');
                        lastQuestion = allQuestions[allQuestions.length - 1];
                        lastQuestion.parentNode.removeChild(lastQuestion);
                    }
                }
                if (data[3] == null){
                    $('.micro-ai-btn-container').css('display', 'none');
                    $('.chat-input').css('display', 'none');
                    let p = document.createElement('p');
                    p.classList.add('notification-btm');
                    p.textContent = data[5];
                    document.querySelectorAll('.chatgpt_wrapper')[document.querySelectorAll('.chatgpt_wrapper').length - 1].appendChild(p);
                } else{
                    $('.chat-input').css('display', 'block');
                    $('.micro-ai-btn-container').css('display', '')
                }
                // document.querySelector('.chat-input').style.display = 'block';
            }
        }
    
        // Start displaying chunks from the first one
        displayNextChunk(0);
    }
    $(function ($) {
        initReports();
        /* Here's where you'd do things on page load. */
    });

}

function ShowInstructions(){
    document.querySelectorAll(".accordion-item").forEach((item) => {
        item.querySelector(".accordion-item-header").addEventListener("click", () => {
            item.classList.toggle("open");
        });
    });
}