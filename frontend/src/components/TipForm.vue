<template>
  <v-dialog v-model="dialog" max-width="600px" persistent>
    <v-form ref="form" v-model="valid" lazy-validation>
      <v-card>
        <v-card-title>
          <span class="headline">{{ caption }}</span>
        </v-card-title>

        <v-card-text>
          <v-text-field
            v-model="editedTip.title"
            label="タイトル"
            :rules="rules.title"
          />

          <v-textarea
            v-model="editedTip.text"
            label="本文"
            rows="15"
          ></v-textarea>

          <v-switch value label="Use" v-model="editedTip.enable"></v-switch>
        </v-card-text>

        <v-card-actions>
          <v-btn color="grey" flat @click="close">Cancel</v-btn>
          <v-spacer />
          <v-btn color="primary" flat @click="save">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </v-dialog>
</template>

<script lang="ts">
import { Component, Emit, Vue } from 'vue-property-decorator';
import { CREATE_TIP, UPDATE_TIP } from '@/graphql/queries';
import { Tip } from '@/types/models';
import { FetchResult } from 'apollo-link';
import { createTip } from '@/graphql/types/createTip';
import { updateTip } from '@/graphql/types/updateTip';

@Component({})
export default class TipForm extends Vue {
  $refs!: {
    form: HTMLFormElement;
  };

  readonly rules = {
    title: [
      (value: string) => !!value || '必須入力です',
      () => this.validate_error('title'),
    ],
    text: [() => this.validate_error('text')],
  };

  readonly defaultTip: Tip = {
    id: '',
    title: '',
    text: '',
    enable: true,
  };

  private dialog: boolean = false;
  private valid = true;
  private errors: { field: string; messages: string[] }[] = [];

  private channelId: String = '';
  private editedTip: Tip = { ...this.defaultTip };

  open(channelId: string, tip: Tip | null = null) {
    this.dialog = true;
    this.valid = true;
    this.errors = [];
    this.$refs.form.resetValidation();

    this.channelId = channelId;
    this.editedTip = {
      ...this.defaultTip,
      ...JSON.parse(JSON.stringify(tip || {})), // deepcopy
    };
  }

  get caption() {
    if (this.editedTip.id) {
      return 'Tips編集';
    } else {
      return 'Tips作成';
    }
  }

  validate_error(field: string): string | boolean {
    let error = this.errors.find(i => i.field == field);
    if (error) {
      return error.messages.join('\n');
    } else {
      return true;
    }
  }

  close() {
    this.dialog = false;
  }

  save() {
    this.errors = [];
    if (this.$refs.form.validate()) {
      let mutation: Promise<FetchResult<createTip | updateTip>>;
      if (!this.editedTip.id) {
        mutation = this.$apollo.mutate<createTip>({
          mutation: CREATE_TIP,
          variables: {
            channelId: this.channelId,
            ...this.editedTip,
          },
          fetchPolicy: 'no-cache',
        });
      } else {
        mutation = this.$apollo.mutate<updateTip>({
          mutation: UPDATE_TIP,
          variables: {
            ...this.editedTip,
          },
          fetchPolicy: 'no-cache',
        });
      }

      mutation
        .then(({ data }) => {
          if (!data || !data.result) {
            throw 'result is null';
          }
          return data.result;
        })
        .then(({ tip, errors }) => {
          if (tip) {
            this.close();
            this.changeTip(tip);
          } else {
            this.valid = false;
            this.errors = errors;
            this.$refs.form.validate();
          }
        })
        .catch(error => {
          console.error(error);
        });
    }
  }

  @Emit()
  changeTip(tip: Tip) {
    return tip;
  }
}
</script>

<style></style>
