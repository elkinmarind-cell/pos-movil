// Configuracion del proyecto Gradle.
//
// El plugin foojay-resolver permite que Gradle descargue por su cuenta el JDK 17
// si el equipo no lo tiene: es lo que evita el clasico "Unsupported class file
// major version" cuando el Java instalado es mas viejo de lo que pide Compose.

pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
        google()
        maven("https://maven.pkg.jetbrains.space/public/p/compose/dev")
    }
}

plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
}

rootProject.name = "pos-movil-kotlin"
