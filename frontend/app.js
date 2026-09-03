const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");


/* =========================
   CHAT MESSAGE
========================= */

function addMessage(message, type, sources = []) {

    const messageDiv = document.createElement("div");

    messageDiv.className = `message ${type}`;


    const avatar = document.createElement("div");

    avatar.className = "avatar";

    avatar.textContent =
        type === "user" ? "You" : "AI";


    const content = document.createElement("div");


    const bubble = document.createElement("div");

    bubble.className = "bubble";


    const paragraph = document.createElement("p");

    paragraph.textContent = message;

    bubble.appendChild(paragraph);


    content.appendChild(bubble);


    /* Sources */

    if (
        type === "bot" &&
        sources.length > 0
    ) {

        const sourceContainer =
            document.createElement("div");

        sourceContainer.className = "sources";


        const sourceTitle =
            document.createElement("div");

        sourceTitle.className = "source-title";

        sourceTitle.textContent = "Sources";


        sourceContainer.appendChild(
            sourceTitle
        );


        sources.forEach(source => {

            const sourceItem =
                document.createElement("div");

            sourceItem.className =
                "source-item";

            sourceItem.textContent =
                `📄 ${source}`;


            sourceContainer.appendChild(
                sourceItem
            );

        });


        content.appendChild(
            sourceContainer
        );
    }


    messageDiv.appendChild(avatar);

    messageDiv.appendChild(content);

    chatBox.appendChild(messageDiv);


    chatBox.scrollTop =
        chatBox.scrollHeight;
}


/* =========================
   SEND MESSAGE
========================= */

async function sendMessage() {

    const message =
        messageInput.value.trim();


    if (!message) {
        return;
    }


    addMessage(
        message,
        "user"
    );


    messageInput.value = "";

    sendButton.disabled = true;


    addMessage(
        "Thinking...",
        "bot"
    );


    try {

        const response =
            await fetch(
                "/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        message: message
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Server error"
            );
        }


        /* Remove Thinking */

        const botMessages =
            document.querySelectorAll(
                ".message.bot"
            );


        const lastBotMessage =
            botMessages[
                botMessages.length - 1
            ];


        if (lastBotMessage) {

            lastBotMessage.remove();
        }


        /* Add actual answer */

        addMessage(
            data.answer,
            "bot",
            data.sources || []
        );


    } catch (error) {

        console.error(
            "Chat error:",
            error
        );


        const botMessages =
            document.querySelectorAll(
                ".message.bot"
            );


        const lastBotMessage =
            botMessages[
                botMessages.length - 1
            ];


        if (lastBotMessage) {

            lastBotMessage.remove();
        }


        addMessage(
            "Sorry, I could not connect to the server.",
            "bot"
        );
    }


    sendButton.disabled = false;

    messageInput.focus();
}


/* =========================
   ENTER KEY
========================= */

function handleKey(event) {

    if (
        event.key === "Enter" &&
        !event.shiftKey
    ) {

        event.preventDefault();

        sendMessage();
    }
}


/* =========================
   NEW CHAT
========================= */

function newChat() {

    chatBox.innerHTML = `

        <div class="message bot">

            <div class="avatar">
                AI
            </div>

            <div class="bubble">

                <p>Hello! 👋</p>

                <p>
                    I can answer questions using
                    the private hospital and
                    company data.
                </p>

            </div>

        </div>

    `;
}


/* =========================
   LOAD DOCUMENTS
========================= */

async function loadDocuments() {

    const documentList =
        document.getElementById(
            "documentList"
        );


    if (!documentList) {

        console.error(
            "documentList element not found"
        );

        return;
    }


    documentList.innerHTML = `
        <div class="empty-documents">
            Loading documents...
        </div>
    `;


    try {

        const response =
            await fetch(
                "/documents"
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        documentList.innerHTML = "";


        if (
            !data.documents ||
            data.documents.length === 0
        ) {

            documentList.innerHTML = `
                <div class="empty-documents">
                    No documents loaded
                </div>
            `;

            return;
        }


        data.documents.forEach(
            doc => {

                const item =
                    document.createElement(
                        "div"
                    );

                item.className =
                    "document-item";


                const info =
                    document.createElement(
                        "div"
                    );

                info.className =
                    "document-info";


                const name =
                    document.createElement(
                        "div"
                    );

                name.className =
                    "document-name";

                name.textContent =
                    `📄 ${doc.source}`;


                const chunks =
                    document.createElement(
                        "div"
                    );

                chunks.className =
                    "document-chunks";

                chunks.textContent =
                    `${doc.chunks} chunks`;


                info.appendChild(name);

                info.appendChild(chunks);


                const deleteButton =
                    document.createElement(
                        "button"
                    );

                deleteButton.className =
                    "delete-document";

                deleteButton.textContent =
                    "🗑";

                deleteButton.title =
                    "Delete document";


                deleteButton.onclick =
                    function () {

                        deleteDocument(
                            doc.source
                        );

                    };


                item.appendChild(info);

                item.appendChild(
                    deleteButton
                );


                documentList.appendChild(
                    item
                );

            }
        );


    } catch (error) {

        console.error(
            "Document loading error:",
            error
        );


        documentList.innerHTML = `
            <div class="empty-documents">
                Failed to load documents
            </div>
        `;
    }
}


/* =========================
   DELETE DOCUMENT
========================= */

async function deleteDocument(source) {

    const confirmed =
        confirm(
            `Delete "${source}" from the knowledge base?`
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `/documents?source=${encodeURIComponent(source)}`,
                {
                    method: "DELETE"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Delete failed"
            );
        }


        addMessage(
            `Document "${source}" was deleted from the private knowledge base.`,
            "bot"
        );


        /*
         * Load the list ONCE after deletion.
         */

        await loadDocuments();


    } catch (error) {

        console.error(
            "Delete error:",
            error
        );


        addMessage(
            `Could not delete "${source}".`,
            "bot"
        );
    }
}


/* =========================
   UPLOAD DOCUMENT
========================= */

async function uploadDocument() {

    const fileInput =
        document.getElementById(
            "fileInput"
        );


    const status =
        document.getElementById(
            "uploadStatus"
        );


    const file =
        fileInput.files[0];


    if (!file) {
        return;
    }


    status.textContent =
        "Uploading...";


    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    try {

        const response =
            await fetch(
                "/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Upload failed"
            );
        }


        status.textContent =
            `✓ ${data.filename} added`;


        addMessage(
            `Document "${data.filename}" has been added to the private knowledge base.`,
            "bot"
        );


        /*
         * Refresh document list ONCE.
         */

        await loadDocuments();


    } catch (error) {

        console.error(
            "Upload error:",
            error
        );


        status.textContent =
            "❌ Upload failed";


        addMessage(
            `Upload error: ${error.message}`,
            "bot"
        );

    }


    fileInput.value = "";
}


/* =========================
   INITIAL LOAD
========================= */

/*
 * Load the document list exactly once
 * when the page starts.
 */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        loadDocuments();

    }
);