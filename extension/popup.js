function scan() {
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        let url = tabs[0].url;

        fetch("http://127.0.0.1:5000/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: "", url: url })
        })
        .then(res => res.json())
        .then(data => {
            document.getElementById("result").innerText =
                "Risk: " + data.risk + "%";
        });
    });
}