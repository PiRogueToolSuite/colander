import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

export default definePreset(Aura, {
  semantic: {
    primary: {
      50: '{purple.50}',
      100: '{purple.100}',
      200: '{purple.200}',
      300: '{purple.300}',
      400: '{purple.400}',
      500: '{purple.500}',
      600: '{purple.600}',
      700: '{purple.700}',
      800: '{purple.800}',
      900: '{purple.900}',
      950: '{purple.950}'
    },
    formField: {
      focusRing: {
        width: '1px',
        style: 'solid',
        color: 'rgb(184, 144.5, 236.5)',
        shadow: '0 0 0 0.25rem rgba(113,34,218,0.25)'
      },
    },
  },
  components: {}
});
