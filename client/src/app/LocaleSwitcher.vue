<template>
  <div class="locale-switcher">
    🌐
    <select v-model="$i18n.locale" @change="setLocale">
      <option value="en">English</option>
      <option value="fr">Français</option>
    </select>
  </div>
</template>

<script>

import i18n from '../i18n'

export default {
  name: "LocaleSwitcher",
  methods: {
    setLocale() {
      console.log('Set language')
      localStorage.setItem("lang", i18n.locale);
    },
  }
}
</script>