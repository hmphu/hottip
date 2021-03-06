<template>
  <v-data-table
    :headers="headers"
    :items="channels"
    :loading="loading"
    no-data-text="なし"
    class="elevation-1"
    hide-actions
    disable-initial-sort
  >
    <template v-slot:items="props">
      <tr span @click="clickChannel(props.item)">
        <td>{{ props.item.rawId }}</td>
        <td class="text-sm-left text-wrap">{{ props.item.name }}</td>
        <td class="text-sm-left text-wrap">
          {{ props.item.description | ellipsis(20) }}
        </td>
        <td>
          <template v-if="props.item.distributors">
            <v-chip
              class="distributor_title"
              color="indigo lighten-1"
              text-color="white"
              v-for="dist in props.item.distributors"
              :key="dist.id"
            >
              {{ distributorTitle(dist) }}
            </v-chip>
          </template>
        </td>
        <td class="font-weight-light">
          {{ props.item.updatedAt | datetime }}
        </td>
      </tr>
    </template>
  </v-data-table>
</template>

<script lang="ts">
import { Component, Prop, Emit, Vue } from 'vue-property-decorator';
import { Channel, Distributor } from '@/types/models';
import { Attribute } from '@/utils/AttributeUtils';

@Component({})
export default class ChannelList extends Vue {
  $refs!: {
    form: HTMLFormElement;
  };

  readonly headers = [
    { text: 'ID', value: 'rawId', width: '30' },
    { text: '名前', value: 'name' },
    { text: '説明', value: 'description', width: '30%' },
    { text: '送信先', value: 'distributors', width: '20%' },
    { text: '更新日付', value: 'createdAt', width: '170' },
  ];

  @Prop() channels!: Channel[];
  @Prop() loading!: boolean;

  @Emit()
  clickChannel(channel: Channel) {
    return channel;
  }

  distributorTitle(dist: Distributor) {
    let attr = new Attribute(dist.attribute);
    return attr.get('channel');
  }
}
</script>

<style lang="stylus">
.text-wrap {
  word-break: break-all;
}

.distributor_title {
  font-size: 85%;
  .v-chip__content {
    height: 24px;
  }
}
</style>
