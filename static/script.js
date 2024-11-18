
function expandSidebar() {
    document.getElementById('sidebar').classList.add('expanded');
}

function collapseSidebar() {
    document.getElementById('sidebar').classList.remove('expanded');
}



function calculateLifePathNumber() {
    let birthdate = document.getElementById('birthdate').value;
    if (!birthdate) {
        alert('請輸入有效的日期');
        return;
    }
    console.log(birthdate);
    // 移除 '-' 並將日期拆分成陣列
    let digits = birthdate.replace(/-/g, '').split('').map(Number);
    console.log("digits:",digits);

    // 計算數字的總和
    let lifePathNumber = digits.reduce((acc, curr) => acc + curr, 0);

    // 如果結果是兩位數，繼續相加直到剩下一位數
    while (lifePathNumber > 9 && lifePathNumber !== 11 && lifePathNumber !== 22 && lifePathNumber !== 33) {
        lifePathNumber = lifePathNumber.toString().split('').map(Number)
            .reduce((acc, curr) => acc + curr, 0);
    }

    // 顯示結果
    if (lifePathNumber !== 11 && lifePathNumber !== 22 && lifePathNumber !== 33){
    document.getElementById('result').innerText = `你的生命靈數是：${lifePathNumber}`;
    }
    else{
        total = lifePathNumber.toString().split('').map(Number)
        .reduce((acc, curr) => acc + curr, 0);
        document.getElementById('result').innerText = `你的生命靈數是：${total}(${lifePathNumber})`;
    }
}
