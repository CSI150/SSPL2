// Get Reference to Our Own Elements

let percent = document.getElementById('percent');
let counter = 0;

setInterval(() => {
    if (counter == 100){
        clearInterval;
    } else{
        counter += 1;
        percent.innerHTML = `${counter}%`;
    }
}, 20);