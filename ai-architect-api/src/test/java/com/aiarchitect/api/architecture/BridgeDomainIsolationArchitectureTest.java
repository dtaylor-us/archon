package com.aiarchitect.api.architecture;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.lang.ArchRule;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

/**
 * ADL-006: API Gateway Service — Bridge Domain Isolation (Soft enforcement).
 *
 * Ensures the bridge domain (client package) has no dependency on the
 * conversation domain (domain package) or chat domain (controller package).
 */
class BridgeDomainIsolationArchitectureTest {

    private static JavaClasses importedClasses;

    @BeforeAll
    static void setUp() {
        importedClasses = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("com.aiarchitect.api");
    }

    @Test
    @DisplayName("ADL-006: Bridge domain has no dependency on Conversation domain")
    void bridge_has_no_dependency_on_conversation() {
        ArchRule rule = noClasses()
                .that().resideInAPackage("com.aiarchitect.api.client..")
                .should().dependOnClassesThat().resideInAPackage("com.aiarchitect.api.domain..")
                .as("ADL-006: Bridge (client) must not depend on Conversation (domain)");

        rule.check(importedClasses);
    }

    @Test
    @DisplayName("ADL-006: Bridge domain has no dependency on Chat domain")
    void bridge_has_no_dependency_on_chat() {
        ArchRule rule = noClasses()
                .that().resideInAPackage("com.aiarchitect.api.client..")
                .should().dependOnClassesThat().resideInAPackage("com.aiarchitect.api.controller..")
                .as("ADL-006: Bridge (client) must not depend on Chat (controller)");

        rule.check(importedClasses);
    }
}
