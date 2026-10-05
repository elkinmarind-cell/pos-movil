import org.jetbrains.compose.desktop.application.dsl.TargetFormat

// Las tres versiones estan fijadas a proposito y van juntas:
//   Kotlin 2.0.21  +  plugin.compose 2.0.21  +  Compose Multiplatform 1.7.3
// Desde Kotlin 2.0 el compilador de Compose dejo de vivir dentro del plugin de
// Compose y pasó a ser `org.jetbrains.kotlin.plugin.compose`, que debe tener
// exactamente la misma version que Kotlin. Cambiar una sola de las tres rompe la
// compilacion con un error que no dice eso.
plugins {
    kotlin("jvm") version "2.0.21"
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21"
    id("org.jetbrains.compose") version "1.7.3"
}

group = "co.cun.posmovil"
version = "1.0.0"

repositories {
    mavenCentral()
    google()
    maven("https://maven.pkg.jetbrains.space/public/p/compose/dev")
}

dependencies {
    // Compose para el sistema operativo donde se compile (Windows, macOS o Linux).
    implementation(compose.desktop.currentOs)
    implementation(compose.material3)

    // Coroutines con despachador de Swing: deja hacer la peticion HTTP fuera del
    // hilo de la interfaz y volver a el para pintar el resultado.
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:1.9.0")

    // Driver JDBC de PostgreSQL. Lo usa el ejemplo de "Query y BD"; la aplicacion
    // habla con la API, no con la base.
    implementation("org.postgresql:postgresql:42.7.4")

    testImplementation(kotlin("test"))
}

kotlin {
    jvmToolchain(17)
}

compose.desktop {
    application {
        mainClass = "pos.MainKt"

        nativeDistributions {
            targetFormats(TargetFormat.Msi, TargetFormat.Deb, TargetFormat.Dmg)
            packageName = "POS-Movil"
            packageVersion = "1.0.0"
            description = "Sistema POS para la gestion y venta de dispositivos moviles"
            copyright = "Elkin Santiago Marin Duarte y Juan David Zabala Plata"
            vendor = "Corporacion Unificada Nacional - CUN"

            windows {
                menu = true
                shortcut = true
                // Identificador fijo: hace que una reinstalacion actualice la
                // version anterior en lugar de dejar dos entradas en el panel de
                // control. Si se cambia, Windows lo toma como otro programa.
                upgradeUuid = "7E6C1A84-2E3F-4C7B-9A41-5D0F6B2C8E13"
            }
        }
    }
}

// --- Los ejemplos de la rubrica ------------------------------------------
// Cada uno tiene su propia funcion main y se ejecuta con una tarea de Gradle:
//   gradlew ventana   gradlew ejemplo   gradlew consulta
fun ejemplo(nombre: String, clase: String, explicacion: String) =
    tasks.register<JavaExec>(nombre) {
        group = "ejemplos de la rubrica"
        description = explicacion
        mainClass.set(clase)
        classpath = sourceSets["main"].runtimeClasspath
        standardInput = System.`in`
    }

ejemplo("ventana", "ejemplos.MiPrimeraVentanaKt",
        "Mi primera ventana en Kotlin (Swing, sin dependencias)")
ejemplo("ejemplo", "ejemplos.EjemploKt",
        "Recorrido por el lenguaje: tipos, nulos, colecciones, clases")
ejemplo("consulta", "ejemplos.QueryBDKt",
        "Consultas a PostgreSQL con JDBC")

tasks.test {
    useJUnitPlatform()
}
