/* Javascript for GuidedRubricXBlock. */
function GuidedRubricXBlock(runtime, element) {

    let chatMsg = document.getElementById('chat-msg');
    let chatLogs = document.getElementById('chat-logs');
    let sendBtn = document.getElementById('send-btn');
    let errorMsg = document.getElementById('error-msg');
    let loadingMsg = document.createElement('div');
    var overlay = document.createElement("div");
    overlay.setAttribute("class", "overlay");
    overlay.setAttribute("id", "overlay-loader");
    var loader = document.createElement("div");
    loader.setAttribute("class", "lds-dual-ring");
    overlay.appendChild(loader);
    loadingMsg.classList.add("loading");
    loadingMsg.appendChild(loader);
    // Handlers
    var handlerUrl = runtime.handlerUrl(element, 'send_message');

    function send_message(message) {
        return $.ajax({
            type: "POST",
            url: handlerUrl,
            data: JSON.stringify({"message": message}),
            contentType:"application/json; charset=utf-8",
            dataType: "json",
        }).done(function(response) {
            if (response.result === 'success') {
                chatLogs.removeChild(loadingMsg);
                console.log(response.response);
                type_message(response.response);
            } else {
                alert("You've reached the end of the exercise. Hope you learned something!");
                chatLogs.removeChild(loadingMsg);
                document.querySelector('.chat-input').style.display = 'block';
            }
        }).fail(function(error) {
            console.log("An error occurred: ", error);
        });
    };

    sendBtn.addEventListener('click', function() {
        if (!chatMsg.value.trim()) {
            errorMsg.textContent = "You should enter prompt";
            return;
        }
        document.querySelector('.chat-input').style.display = 'none';
        errorMsg.textContent = "";
        let newMsg = document.createElement('div');
        let linebreak = document.createElement('br');
        newMsg.textContent = chatMsg.value;
        newMsg.classList.add("my-msg");
        chatLogs.appendChild(newMsg);
        chatLogs.appendChild(linebreak);
        chatLogs.appendChild(loadingMsg);

        chatMsg.value = "";
        // Call the Python function with the message as input
        send_message(newMsg.textContent);
    });
    function type_message(message) {
        let i = 0;
        let aiMsg = document.createElement('div');
        let question = document.createElement('p');
        aiMsg.classList.add("ai-msg");
        question.classList.add("questions");
        chatLogs.appendChild(aiMsg);
        let typing = setInterval(function() {
            if (i < message.length) {
                aiMsg.textContent = message[0];
                question.textContent = "testing ";
                chatLogs.appendChild(question);
                document.querySelector('.chat-input').style.display = 'block';
                i++;
            } else {
                clearInterval(typing);
            }
        }, 10);
    }

    $(function ($) {
        /* Here's where you'd do things on page load. */
    });

}

