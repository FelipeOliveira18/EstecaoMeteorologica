const FIREBASE_URL =
    "https://trabalho-26cb3-default-rtdb.firebaseio.com";

const FIREBASE_PATH = "/leitura_atual.json";

const INTERVALO = 5000;


// ==========================================
// FUNCOES AUXILIARES
// ==========================================

function elemento(id) {
    return document.getElementById(id);
}


function atualizarTexto(id, valor) {

    const el = elemento(id);

    if (el) {
        el.textContent = valor;
    }

}


function numeroValido(valor) {

    if (
        valor === null ||
        valor === undefined ||
        valor === ""
    ) {
        return null;
    }

    const numero = Number(valor);

    return Number.isFinite(numero) ? numero : null;

}


function formatar(valor, casas = 1) {

    const numero = numeroValido(valor);

    if (numero === null) {
        return "--";
    }

    return numero.toLocaleString("pt-BR", {
        maximumFractionDigits: casas,
        minimumFractionDigits: casas
    });

}


function primeiroValorValido(...valores) {

    for (const valor of valores) {

        if (numeroValido(valor) !== null) {
            return valor;
        }

    }

    return null;

}


// ==========================================
// STATUS DA CONEXAO
// ==========================================

function atualizarConexao(estado, mensagem) {

    const indicador = elemento("statusDot");

    if (indicador) {

        indicador.className = "status-dot";

        if (estado) {
            indicador.classList.add(estado);
        }

    }

    atualizarTexto("conexaoStatus", mensagem);

}


// ==========================================
// IDENTIFICAR CONDICAO AMBIENTAL
// ==========================================

function estimarCondicao(temperatura, umidade) {

    const t = numeroValido(temperatura);
    const u = numeroValido(umidade);

    if (t === null || u === null) {
        return "Sem dados";
    }

    if (t >= 30 && u >= 70) {
        return "Quente e úmido";
    }

    if (t >= 30) {
        return "Quente";
    }

    if (t <= 18 && u >= 70) {
        return "Frio e úmido";
    }

    if (t <= 18) {
        return "Frio";
    }

    if (u >= 75) {
        return "Úmido";
    }

    if (u <= 35) {
        return "Seco";
    }

    return "Ameno";

}


// ==========================================
// MOSTRAR DADOS DOS SENSORES
// ==========================================

function mostrarDados(dados) {

    // TEMPERATURA DHT22

    atualizarTexto(
        "temperatura",
        formatar(dados.temperatura)
    );


    // UMIDADE DHT22

    atualizarTexto(
        "umidade",
        formatar(dados.umidade)
    );


    // PRESSAO BMP280

    const pressao = primeiroValorValido(
        dados.pressao_hpa,
        dados.pressao
    );

    atualizarTexto(
        "pressao",
        formatar(pressao, 2)
    );


    // ALTITUDE BMP280

    const altitude = primeiroValorValido(
        dados.altitude_m,
        dados.altitude
    );

    atualizarTexto(
        "altitude",
        formatar(altitude, 1)
    );


    // LUMINOSIDADE LDR

    atualizarTexto(
        "luz",
        formatar(dados.luminosidade, 0)
    );


    // MQ135 ANALOGICO

    const arAnalogico = primeiroValorValido(
        dados.mq135_analogico,
        dados.mq135_analog,
        dados.co2
    );

    atualizarTexto(
        "arAnalogico",
        formatar(arAnalogico, 0)
    );


    // CONDICAO AMBIENTAL

    atualizarTexto(
        "clima",
        estimarCondicao(
            dados.temperatura,
            dados.umidade
        )
    );


    // ======================================
    // BARRA DE UMIDADE
    // ======================================

    const barra = elemento("barraUmidade");

    const umidade = numeroValido(dados.umidade);

    if (barra) {

        barra.style.width =
            umidade === null
                ? "0%"
                : Math.max(0, Math.min(100, umidade)) + "%";

    }


    // ======================================
    // ESTADO DIGITAL DO MQ135
    // ======================================

    const digital = numeroValido(
        dados.mq135_digital
    );

    const airDot = elemento("airDot");

    if (digital === null) {

        atualizarTexto(
            "arDigital",
            "Sem leitura"
        );

        atualizarTexto(
            "arDescricao",
            "O sensor nao retornou um valor."
        );

        if (airDot) {
            airDot.className = "air-dot";
        }

    } else {

        atualizarTexto(
            "arDigital",
            "Estado lógico: " + digital
        );

        atualizarTexto(
            "arDescricao",
            digital === 1
                ? "Saída digital ativada."
                : "Saída digital desativada."
        );

        if (airDot) {

            airDot.className =
                "air-dot " +
                (digital === 1
                    ? "ativado"
                    : "desativado");

        }

    }


    // ======================================
    // INFORMACOES DO SISTEMA
    // ======================================

    atualizarTexto(
        "ultimoUpdate",
        new Date().toLocaleString("pt-BR")
    );

    atualizarTexto(
        "firebaseStatus",
        "Conectado"
    );

    atualizarConexao(
        "conectado",
        "Estação conectada"
    );

    console.log(
        "Dados recebidos do Firebase:",
        dados
    );

}


// ==========================================
// BUSCAR DADOS NO FIREBASE
// ==========================================

async function buscarDados() {

    const botao = elemento("recarregar");

    if (botao) {
        botao.disabled = true;
    }

    try {

        const url =
            FIREBASE_URL +
            FIREBASE_PATH +
            "?t=" +
            Date.now();

        const resposta = await fetch(url, {

            method: "GET",

            cache: "no-store"

        });


        if (!resposta.ok) {

            throw new Error(
                "Erro HTTP: " + resposta.status
            );

        }


        const dados = await resposta.json();


        if (
            !dados ||
            typeof dados !== "object" ||
            Array.isArray(dados)
        ) {

            throw new Error(
                "Dados invalidos no Firebase."
            );

        }


        mostrarDados(dados);


    } catch (erro) {

        console.error(
            "Erro ao buscar dados:",
            erro
        );

        atualizarConexao(
            "erro",
            "Falha na conexão com Firebase"
        );

        atualizarTexto(
            "firebaseStatus",
            "Erro na conexão"
        );


    } finally {

        if (botao) {
            botao.disabled = false;
        }

    }

}


// ==========================================
// BOTAO RECARREGAR
// ==========================================

const botaoAtualizar = elemento("recarregar");

if (botaoAtualizar) {

    botaoAtualizar.addEventListener(
        "click",
        buscarDados
    );

}


// ==========================================
// INICIALIZACAO AUTOMATICA
// ==========================================

buscarDados();

setInterval(
    buscarDados,
    INTERVALO
);