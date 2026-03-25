/* Onboarding configuration per role for Contrudesk (client-side only) */
window.OnboardingGuideConfig = {
  version: 1,
  roles: {
    admin: {
      steps: [
        { intro: "Bienvenido 👋 Como administrador, configuras la organización y gestionas el acceso." },
        { element: '[data-onb="nav-admin-dashboard"]', intro: 'Tu panel principal con indicadores clave.' },
        { element: '[data-onb="nav-admin-users"]', intro: 'Gestiona usuarios, roles y permisos.' },
        { element: '[data-onb="nav-admin-projects"]', intro: 'Crea y administra proyectos.' },
        { element: '[data-onb="nav-admin-assign"]', intro: 'Asigna usuarios a proyectos.' },
        { element: '[data-onb="nav-admin-incidencias"]', intro: 'Revisa y gestiona incidencias.' },
        { element: '[data-onb="nav-admin-reportes"]', intro: 'Accede a reportes técnicos.' },
        { element: '[data-onb="nav-admin-plantillas"]', intro: 'Define plantillas de documentos.' },
        { element: '[data-onb="nav-admin-flujos"]', intro: 'Configura flujos de aprobación.' },
        { intro: 'Listo. Puedes volver a esta guía desde el botón “Guía” en el encabezado.' }
      ]
    },
    editor: {
      steps: [
        { intro: 'Bienvenido 👋 Como editor, gestionas documentos, avances y reportes.' },
        { element: '[data-onb="nav-editor-dashboard"]', intro: 'Acceso a documentos y planos.' },
        { element: '[data-onb="nav-editor-proyectos"]', intro: 'Gestiona el avance de obra.' },
        { element: '[data-onb="nav-editor-reportes"]', intro: 'Crea y revisa reportes técnicos.' },
        { element: '[data-onb="nav-editor-plantillas"]', intro: 'Usa y gestiona plantillas.' },
        { element: '[data-onb="nav-editor-flujos"]', intro: 'Sigue flujos de trabajo asignados.' },
        { intro: 'Eso es todo. Reabre la guía con el botón “Guía”.' }
      ]
    },
    miembro: {
      steps: [
        { intro: 'Bienvenido 👋 Como miembro, verás tus tareas y reportarás avances.' },
        { element: '[data-onb="nav-miembro-tareas"]', intro: 'Consulta tus tareas asignadas.' },
        { element: '[data-onb="nav-miembro-proyectos"]', intro: 'Registra avances de tus proyectos.' },
        { element: '[data-onb="nav-miembro-incidencias"]', intro: 'Reporta incidencias cuando sea necesario.' },
        { intro: 'Puedes volver a ver esta guía cuando quieras desde “Guía”.' }
      ]
    },
    lector: {
      steps: [
        { intro: 'Bienvenido 👋 Como lector, revisas proyectos y documentos.' },
        { element: '[data-onb="nav-lector-dashboard"]', intro: 'Vista general de proyectos.' },
        { element: '[data-onb="nav-lector-documentos"]', intro: 'Consulta documentos y planos.' },
        { intro: 'Guía disponible nuevamente desde el botón “Guía”.' }
      ]
    },
    mensajero: {
      steps: [
        { intro: 'Bienvenido 👋 Como mensajero, gestiona comunicaciones.' },
        { element: '[data-onb="nav-mensajero-dashboard"]', intro: 'Accede a tus mensajes.' },
        { intro: 'Puedes reabrir esta guía con el botón “Guía”.' }
      ]
    },
    superadmin: {
      steps: [
        { intro: 'Bienvenido 👋 Como superadmin, tienes una vista global y control total.' },
        { element: '[data-onb="nav-superadmin-dashboard"]', intro: 'Ingresa a tu panel principal.' },
        { intro: 'Desde aquí podrás configurar la plataforma. Reabre la guía con “Guía”.' }
      ]
    },
    invitado: {
      steps: [
        { intro: 'Bienvenido 👋 Como invitado, accedes a tus proyectos y documentos.' },
        { element: '[data-onb="nav-invitado-dashboard"]', intro: 'Listado de tus proyectos.' },
        { element: '[data-onb="nav-invitado-documentos"]', intro: 'Documentos de los proyectos.' },
        { element: '[data-onb="nav-invitado-avances"]', intro: 'Revisa avances de obra.' },
        { intro: 'Puedes volver a esta guía con el botón “Guía”.' }
      ]
    }
  }
};
