import { createApp } from "vue";
import { createPinia } from "pinia";
import {
  ElAlert,
  ElButton,
  ElDatePicker,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from "element-plus";
import "element-plus/dist/index.css";

import App from "./App.vue";
import { router } from "./router";
import "./styles.css";

const app = createApp(App).use(createPinia()).use(router);
for (const component of [
  ElAlert,
  ElButton,
  ElDatePicker,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElInputNumber,
  ElOption,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
]) {
  app.component(component.name ?? "", component);
}
app.use(ElLoading);
app.mount("#app");
