<template>
  <v-dialog v-model="dialog" max-width="500px" persistent>
    <v-card>
      <v-card-title>
        <span class="headline">{{ caption }}</span>
      </v-card-title>

      <v-form ref="form" v-model="valid" lazy-validation>
        <v-card-text>
          <v-text-field
            :rules="rules.name"
            v-model="editedChannel.name"
            label="名前"
          ></v-text-field>
          <v-textarea
            v-model="editedChannel.description"
            label="説明"
          ></v-textarea>
        </v-card-text>
      </v-form>

      <v-card-actions>
        <v-btn color="grey" flat @click="close">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="primary" flat @click="save">Save</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script lang="ts">
import { Component, Emit, Vue } from 'vue-property-decorator';
import { CREATE_CHANNEL, UPDATE_CHANNEL } from '@/graphql/queries';
import { createChannel } from '@/graphql/types/createChannel';
import { updateChannel } from '@/graphql/types/updateChannel';
import { FetchResult } from 'apollo-link';
import { Channel } from '@/types/models';

@Component({})
export default class ChannelForm extends Vue {
  $refs!: {
    form: HTMLFormElement;
  };

  readonly rules = {
    name: [
      (value: string) => !!value || '必須入力です',
      () => this.validate_error('name'),
    ],
  };

  readonly defaultChannel = {
    id: '',
    name: '',
    description: '',
  };

  private dialog = false;
  private valid = true;
  private errors: { field: string; messages: string[] }[] = [];

  private editedChannel = { ...this.defaultChannel };

  open(channel: Channel | null = null) {
    this.dialog = true;
    this.valid = true;
    this.errors = [];
    this.$refs.form.resetValidation();

    this.editedChannel = { ...this.defaultChannel, ...channel };
  }

  get caption() {
    if (this.editedChannel.id) {
      return 'チャンネル編集';
    } else {
      return 'チャンネル作成';
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
      let mutation: Promise<FetchResult<createChannel | updateChannel>>;
      if (!this.editedChannel.id) {
        mutation = this.$apollo.mutate<createChannel>({
          mutation: CREATE_CHANNEL,
          variables: {
            ...this.editedChannel,
          },
          fetchPolicy: 'no-cache',
        });
      } else {
        mutation = this.$apollo.mutate<updateChannel>({
          mutation: UPDATE_CHANNEL,
          variables: {
            ...this.editedChannel,
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
        .then(({ channel, errors }) => {
          if (channel) {
            this.close();
            this.changeChannel(channel);
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
  changeChannel(channel: Channel) {
    return channel;
  }
}
</script>

<style></style>
